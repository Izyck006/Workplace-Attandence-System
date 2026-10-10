using System;
using System.Collections.Generic;
using System.Windows.Forms;

namespace IBScanUltimate_SampleForCSharp
{
    static class Program
    {
        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            string netVersion = System.Runtime.InteropServices.RuntimeEnvironment.GetSystemVersion();
            if (netVersion[1] >= '2')
                Application.Run(new SDKMainForm());
            else
                MessageBox.Show("SDK works with .Net Version 2.0 and higher");
        }
    }
}
