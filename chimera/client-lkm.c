// lkm_dns_client.c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/kthread.h>
#include <linux/delay.h>
#include <linux/slab.h>
#include <linux/in.h>
#include <linux/net.h>
#include <linux/string.h>
#include <linux/types.h>

#include <net/sock.h>
#include <net/net_namespace.h>

#if __has_include(<asm/unaligned.h>)
#include <asm/unaligned.h>
#elif __has_include(<linux/unaligned.h>)
#include <linux/unaligned.h>
#endif

#define DNS_SERVER_IP      0x0100007F  // 127.0.0.1 (little endian)
#define DNS_SERVER_PORT    53

#define QUERY_INTERVAL_MS  60000
#define RECV_TIMEOUT_MS    2000

#define DNS_QTYPE_A        1
#define DNS_QTYPE_TXT      16
#define DNS_QCLASS_IN      1

#define DNS_MAX_PACKET     512
#define DNS_MAX_RESULTS    8
#define DNS_MAX_TXT_LEN    256

static struct task_struct *dns_thread;

struct dns_hdr {
	__be16 id;
	__be16 flags;
	__be16 qdcount;
	__be16 ancount;
	__be16 nscount;
	__be16 arcount;
} __packed;

struct dns_result {
	int a_count;
	__be32 a_records[DNS_MAX_RESULTS];

	int txt_count;
	char txt_records[DNS_MAX_RESULTS][DNS_MAX_TXT_LEN];
};

static int encode_qname(u8 *buf, size_t buflen, const char *domain)
{
	const char *label = domain;
	const char *dot;
	u8 *p = buf;
	size_t label_len;

	while (*label) {
		dot = strchr(label, '.');

		if (dot)
			label_len = dot - label;
		else
			label_len = strlen(label);

		if (label_len == 0 || label_len > 63)
			return -EINVAL;

		if ((p - buf) + 1 + label_len >= buflen)
			return -ENOSPC;

		*p++ = label_len;
		memcpy(p, label, label_len);
		p += label_len;

		if (!dot)
			break;

		label = dot + 1;
	}

	if ((p - buf) + 1 > buflen)
		return -ENOSPC;

	*p++ = 0;

	return p - buf;
}

static int build_dns_query(u8 *buf, size_t buflen, const char *domain, u16 qtype)
{
	struct dns_hdr *hdr;
	u8 *p;
	int qname_len;

	if (!buf || !domain)
		return -EINVAL;

	if (qtype != DNS_QTYPE_A && qtype != DNS_QTYPE_TXT)
		return -EINVAL;

	if (buflen < sizeof(*hdr))
		return -EINVAL;

	memset(buf, 0, buflen);

	hdr = (struct dns_hdr *)buf;
	hdr->id      = htons(0x1234);
	hdr->flags   = htons(0x0100); // standard query, recursion desired
	hdr->qdcount = htons(1);

	p = buf + sizeof(*hdr);

	qname_len = encode_qname(p, buflen - sizeof(*hdr), domain);
	if (qname_len < 0)
		return qname_len;

	p += qname_len;

	if ((p - buf) + 4 > buflen)
		return -ENOSPC;

	// QTYPE
	*p++ = qtype >> 8;
	*p++ = qtype & 0xff;

	// QCLASS = IN
	*p++ = 0x00;
	*p++ = DNS_QCLASS_IN;

	return p - buf;
}

static int dns_skip_name(const u8 *buf, int len, int offset)
{
	int steps = 0;

	while (offset < len) {
		u8 c = buf[offset];

		if (c == 0) {
			offset++;
			return offset;
		}

		/*
		 * DNS compression pointer.
		 * Top two bits set means this name is a two-byte pointer.
		 */
		if ((c & 0xC0) == 0xC0) {
			if (offset + 1 >= len)
				return -EINVAL;

			offset += 2;
			return offset;
		}

		/*
		 * Anything else with top bits set is invalid/reserved here.
		 */
		if ((c & 0xC0) != 0x00)
			return -EINVAL;

		offset += 1 + c;

		if (offset > len)
			return -EINVAL;

		if (++steps > 128)
			return -EINVAL;
	}

	return -EINVAL;
}

static int parse_dns_response(const u8 *buf, int len, u16 expected_qtype,
			      struct dns_result *result)
{
	const struct dns_hdr *hdr;
	u16 id;
	u16 flags;
	u16 qdcount;
	u16 ancount;
	u16 rcode;
	int offset;
	int i;

	if (!buf || !result)
		return -EINVAL;

	memset(result, 0, sizeof(*result));

	if (len < sizeof(*hdr))
		return -EINVAL;

	hdr = (const struct dns_hdr *)buf;

	id      = ntohs(hdr->id);
	flags   = ntohs(hdr->flags);
	qdcount = ntohs(hdr->qdcount);
	ancount = ntohs(hdr->ancount);
	rcode   = flags & 0x000f;

	pr_info("lkm_dns_client: response len=%d id=0x%04x qd=%u an=%u rcode=%u\n",
		len, id, qdcount, ancount, rcode);

	if (rcode != 0)
		return -ENOENT;

	offset = sizeof(*hdr);

	/*
	 * Skip question section.
	 */
	for (i = 0; i < qdcount; i++) {
		offset = dns_skip_name(buf, len, offset);
		if (offset < 0)
			return offset;

		if (offset + 4 > len)
			return -EINVAL;

		offset += 4; // QTYPE + QCLASS
	}

	/*
	 * Parse answer section.
	 */
	for (i = 0; i < ancount; i++) {
		u16 type;
		u16 class;
		u32 ttl;
		u16 rdlength;
		const u8 *rdata;

		offset = dns_skip_name(buf, len, offset);
		if (offset < 0)
			return offset;

		if (offset + 10 > len)
			return -EINVAL;

		type = get_unaligned_be16(buf + offset);
		offset += 2;

		class = get_unaligned_be16(buf + offset);
		offset += 2;

		ttl = get_unaligned_be32(buf + offset);
		offset += 4;

		rdlength = get_unaligned_be16(buf + offset);
		offset += 2;

		if (offset + rdlength > len)
			return -EINVAL;

		rdata = buf + offset;

		pr_info("lkm_dns_client: answer type=%u class=%u ttl=%u rdlength=%u\n",
			type, class, ttl, rdlength);

		if (class == DNS_QCLASS_IN &&
		    type == DNS_QTYPE_A &&
		    expected_qtype == DNS_QTYPE_A &&
		    rdlength == 4) {
			if (result->a_count < DNS_MAX_RESULTS) {
				memcpy(&result->a_records[result->a_count], rdata, 4);
				result->a_count++;
			}
		}

		if (class == DNS_QCLASS_IN &&
		    type == DNS_QTYPE_TXT &&
		    expected_qtype == DNS_QTYPE_TXT &&
		    rdlength > 0) {
			if (result->txt_count < DNS_MAX_RESULTS) {
				int txt_index = result->txt_count;
				int pos = 0;
				int rpos = 0;

				/*
				 * TXT RDATA is one or more length-prefixed strings.
				 */
				while (rpos < rdlength && pos < DNS_MAX_TXT_LEN - 1) {
					u8 txt_len = rdata[rpos++];
					int copy_len;

					if (rpos + txt_len > rdlength)
						break;

					copy_len = min_t(int,
							 txt_len,
							 DNS_MAX_TXT_LEN - 1 - pos);

					memcpy(&result->txt_records[txt_index][pos],
					       &rdata[rpos],
					       copy_len);

					pos += copy_len;
					rpos += txt_len;

					if (rpos < rdlength && pos < DNS_MAX_TXT_LEN - 1)
						result->txt_records[txt_index][pos++] = ' ';
				}

				result->txt_records[txt_index][pos] = '\0';
				result->txt_count++;
			}
		}

		offset += rdlength;
	}

	return 0;
}

/*
 * Main reusable client-side function.
 *
 * domain:
 *   Example: "google.com"
 *
 * qtype:
 *   DNS_QTYPE_A   for A records
 *   DNS_QTYPE_TXT for TXT records
 *
 * result:
 *   Filled with A records or TXT records depending on qtype.
 */
static int lkm_dns_query(const char *domain, u16 qtype, struct dns_result *result)
{
	struct socket *sock = NULL;
	struct sockaddr_in addr;
	struct msghdr msg;
	struct kvec iov;
	u8 *tx = NULL;
	u8 *rx = NULL;
	int tx_len;
	int ret;

	if (!domain || !result)
		return -EINVAL;

	if (qtype != DNS_QTYPE_A && qtype != DNS_QTYPE_TXT)
		return -EINVAL;

	tx = kzalloc(DNS_MAX_PACKET, GFP_KERNEL);
	rx = kzalloc(DNS_MAX_PACKET, GFP_KERNEL);

	if (!tx || !rx) {
		ret = -ENOMEM;
		goto out;
	}

	tx_len = build_dns_query(tx, DNS_MAX_PACKET, domain, qtype);
	if (tx_len < 0) {
		ret = tx_len;
		goto out;
	}

	ret = sock_create_kern(&init_net, AF_INET, SOCK_DGRAM, IPPROTO_UDP, &sock);
	if (ret < 0) {
		pr_info("lkm_dns_client: sock_create_kern failed: %d\n", ret);
		goto out;
	}

	sock->sk->sk_rcvtimeo = msecs_to_jiffies(RECV_TIMEOUT_MS);

	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_port = htons(DNS_SERVER_PORT);
	addr.sin_addr.s_addr = htonl(DNS_SERVER_IP);

	memset(&msg, 0, sizeof(msg));
	msg.msg_name = &addr;
	msg.msg_namelen = sizeof(addr);

	iov.iov_base = tx;
	iov.iov_len = tx_len;

	ret = kernel_sendmsg(sock, &msg, &iov, 1, tx_len);
	if (ret < 0) {
		pr_info("lkm_dns_client: send failed: %d\n", ret);
		goto out_release;
	}

	pr_info("lkm_dns_client: sent %s query for %s to 127.0.0.1:53\n",
		qtype == DNS_QTYPE_A ? "A" : "TXT",
		domain);

	memset(&msg, 0, sizeof(msg));
	memset(&addr, 0, sizeof(addr));

	msg.msg_name = &addr;
	msg.msg_namelen = sizeof(addr);

	iov.iov_base = rx;
	iov.iov_len = DNS_MAX_PACKET;

	ret = kernel_recvmsg(sock, &msg, &iov, 1, DNS_MAX_PACKET, 0);
	if (ret < 0) {
		pr_info("lkm_dns_client: recv failed or timed out: %d\n", ret);
		goto out_release;
	}

	ret = parse_dns_response(rx, ret, qtype, result);

out_release:
	sock_release(sock);

out:
	kfree(tx);
	kfree(rx);
	return ret;
}

static void print_dns_result(u16 qtype, struct dns_result *result)
{
	int i;

	if (!result)
		return;

	if (qtype == DNS_QTYPE_A) {
		if (result->a_count == 0) {
			pr_info("lkm_dns_client: no A records returned\n");
			return;
		}

		for (i = 0; i < result->a_count; i++) {
			pr_info("lkm_dns_client: A result: %pI4\n",
				&result->a_records[i]);
		}
	}

	if (qtype == DNS_QTYPE_TXT) {
		if (result->txt_count == 0) {
			pr_info("lkm_dns_client: no TXT records returned\n");
			return;
		}

		for (i = 0; i < result->txt_count; i++) {
			pr_info("lkm_dns_client: TXT result: \"%s\"\n",
				result->txt_records[i]);
		}
	}
}

static int dns_thread_fn(void *data)
{
	bool request_txt = false;

	pr_info("lkm_dns_client: thread started\n");

	while (!kthread_should_stop()) {
		struct dns_result result;
		u16 qtype;
		int ret;
		int slept = 0;

		/*
		 * Flip between A and TXT each loop.
		 *
		 * To only request A:
		 *   qtype = DNS_QTYPE_A;
		 *
		 * To only request TXT:
		 *   qtype = DNS_QTYPE_TXT;
		 */
		qtype = request_txt ? DNS_QTYPE_TXT : DNS_QTYPE_A;

		ret = lkm_dns_query("google.com", qtype, &result);
		if (ret == 0)
			print_dns_result(qtype, &result);
		else
			pr_info("lkm_dns_client: query failed: %d\n", ret);

		request_txt = !request_txt;

		/*
		 * Sleep in 1-second chunks so rmmod can stop the thread promptly.
		 */
		while (slept < QUERY_INTERVAL_MS && !kthread_should_stop()) {
			msleep_interruptible(1000);
			slept += 1000;
		}
	}

	pr_info("lkm_dns_client: thread stopping\n");
	return 0;
}

static int __init lkm_dns_client_init(void)
{
	pr_info("lkm_dns_client: loading\n");

	dns_thread = kthread_run(dns_thread_fn, NULL, "lkm_dns_client");
	if (IS_ERR(dns_thread)) {
		int ret = PTR_ERR(dns_thread);

		pr_info("lkm_dns_client: kthread_run failed: %d\n", ret);
		dns_thread = NULL;
		return ret;
	}

	return 0;
}

static void __exit lkm_dns_client_exit(void)
{
	pr_info("lkm_dns_client: unloading\n");

	if (dns_thread) {
		kthread_stop(dns_thread);
		dns_thread = NULL;
	}

	pr_info("lkm_dns_client: unloaded\n");
}

module_init(lkm_dns_client_init);
module_exit(lkm_dns_client_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("example");
MODULE_DESCRIPTION("Educational LKM DNS client supporting A and TXT queries to 127.0.0.1");