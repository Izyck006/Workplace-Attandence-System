using System;
using System.Runtime.InteropServices;
using IBscanUltimate;

namespace ScannerBridge
{
    class Program
    {
        static void Main(string[] args)
        {
            try
            {
                int deviceCount = 0;
                int nRc = DLL.IBSU_GetDeviceCount(ref deviceCount);
                if (nRc != DLL.IBSU_STATUS_OK || deviceCount == 0)
                {
                    Console.WriteLine("ERROR: No devices found.");
                    return;
                }

                int handle = -1;
                nRc = DLL.IBSU_OpenDevice(0, ref handle);
                if (nRc != DLL.IBSU_STATUS_OK)
                {
                    Console.WriteLine("ERROR: Cannot open device.");
                    return;
                }

                // Simulate getting image... (This is a simplified bridge for testing)
                // In production, we'd use IBSU_BGetImage or IBSU_BeginCaptureImage
                Console.WriteLine("SUCCESS: Template Data Base64 (Mock)");

                DLL.IBSU_CloseDevice(handle);
            }
            catch (Exception ex)
            {
                Console.WriteLine("ERROR: " + ex.Message);
            }
        }
    }
}
