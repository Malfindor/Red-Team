#include <windows.h>
#include <stdlib.h>
#include <time.h>

DWORD WINAPI WorkerThread(LPVOID lpParam)
{
    srand((unsigned int)time(NULL));

    while (true)
    {
        // Random delay between 60 and 120 seconds
        int delay = (rand() % 61 + 60) * 1000;

        Sleep(delay);

        MessageBoxW(
            NULL,
            L"Good soup",
            L"Info",
            MB_OK | MB_ICONINFORMATION
        );
    }

    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ulReason, LPVOID lpReserved)
{
    switch (ulReason)
    {
        case DLL_PROCESS_ATTACH:
        {
            DisableThreadLibraryCalls(hModule);

            HANDLE thread = CreateThread(
                NULL,
                0,
                WorkerThread,
                NULL,
                0,
                NULL
            );

            if (thread)
                CloseHandle(thread);

            break;
        }
    }

    return TRUE;
}