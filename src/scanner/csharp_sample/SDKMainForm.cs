using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using System.Threading;
using IBscanUltimate;
using System.Runtime.InteropServices;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.IO;

namespace IBScanUltimate_SampleForCSharp
{
    public partial class SDKMainForm : Form
    {
        private struct CaptureInfo
        {
            public string			    PreCaptureMessage;		// to display on fingerprint window
            public string			    PostCaptuerMessage;		// to display on fingerprint window
            public DLL.IBSU_ImageType	ImageType;				// capture mode
            public int				    NumberOfFinger;			// number of finger count
            public string			    fingerName;				// finger name (e.g left thumbs, left index ... )
            public DLL.IBSM_FingerPosition fingerPosition;		// Finger position. e.g Right Thumb, Right Index finger
        }

        private struct ThreadParam
        {
            public IntPtr   pParentHandle;
            public IntPtr   pFrameImageHandle;
            public int      devIndex;
        }

        public static DialogResult InputBox(string title, string content, ref string value)
        {
            Form form = new Form();
            Label label = new Label();
            TextBox textBox = new TextBox();
            Button buttonOk = new Button();
            Button buttonCancel = new Button();

            form.ClientSize = new Size(300, 100);
            form.Controls.AddRange(new Control[] { label, textBox, buttonOk, buttonCancel });
            form.FormBorderStyle = FormBorderStyle.FixedDialog;
            form.StartPosition = FormStartPosition.CenterScreen;
            form.MaximizeBox = false;
            form.MinimizeBox = false;
            form.AcceptButton = buttonOk;
            form.CancelButton = buttonCancel;

            form.Text = title;
            label.Text = content;
            textBox.Text = value;
            buttonOk.Text = "Apply";
            buttonCancel.Text = "Cancel";

            buttonOk.DialogResult = DialogResult.OK;
            buttonCancel.DialogResult = DialogResult.Cancel;

            label.SetBounds(5, 17, 100, 20);
            textBox.SetBounds(5, 40, 280, 20);
            buttonOk.SetBounds(135, 70, 70, 20);
            buttonCancel.SetBounds(215, 70, 70, 20);

            textBox.Text = value;

            DialogResult dialogResult = form.ShowDialog();

            value = textBox.Text;
            return dialogResult;
        }


        // Capture sequence definitions
        private const string CAPTURE_SEQ_FLAT_SINGLE_FINGER	= "Single flat finger";
        private const string CAPTURE_SEQ_ROLL_SINGLE_FINGER = "Single rolled finger";
        private const string CAPTURE_SEQ_2_FLAT_FINGERS = "2 flat fingers";
        private const string CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS = "10 single flat fingers";
        private const string CAPTURE_SEQ_10_SINGLE_ROLLED_FINGERS = "10 single rolled fingers";
        private const string CAPTURE_SEQ_4_FLAT_FINGERS = "4 flat fingers";
        private const string CAPTURE_SEQ_10_FLAT_WITH_4_FINGER_SCANNER = "10 flat fingers with 4-finger scanner";

        private const string CAPTURE_SEQ_ROLL_SINGLE_FINGERTIP = "Single rolled fingertip";
        private const string CAPTURE_SEQ_FLAT_SINGLE_JOINT     = "Single flat joint";
        private const string CAPTURE_SEQ_ROLL_SINGLE_JOINT     = "Single rolled joint";
        private const string CAPTURE_SEQ_FLAT_SINGLE_HYPOTHENAR = "Single flat hypothenar";
        private const string CAPTURE_SEQ_ROLL_SINGLE_THENAR     = "Single rolled thenar";
        private const string CAPTURE_SEQ_FLAT_SINGLE_WRITERS_PALM = "Single flat writer's palm";
        private const string CAPTURE_SEQ_FLAT_SINGLE_UPPER_HALFPALM = "Single flat upper halfpalm";
        private const string CAPTURE_SEQ_FLAT_SINGLE_LOWER_HALFPALM = "Single flat lower halfpalm";
        private const string CAPTURE_SEQ_FLAT_442 = "4-4-2 flat";
        private const string CAPTURE_SEQ_FLAT_TWO_HAND_HALFPALM = "HalfPalm for two hands";

        // Beep definitions
        private const int __BEEP_FAIL__ = 0;
        private const int __BEEP_SUCCESS__ = 1;
        private const int __BEEP_OK__ = 2;
        private const int __BEEP_DEVICE_COMMUNICATION_BREAK__ = 3;

        // LED color definitions
        private const int __LED_COLOR_NONE__ = 0;
        private const int __LED_COLOR_GREEN__ = 1;
        private const int __LED_COLOR_RED__ = 2;
        private const int __LED_COLOR_YELLOW__ = 3;

        // Key button definitions
        private const int __LEFT_KEY_BUTTON__ = 1;
        private const int __RIGHT_KEY_BUTTON__ = 2;

        static Thread m_initThread;
        static Object m_sync = new Object();

        private DLL.IBSU_Callback m_callbackDeviceCommunicationBreak = null;
        private DLL.IBSU_CallbackPreviewImage m_callbackPreviewImage = null;
        private DLL.IBSU_CallbackFingerCount m_callbackFingerCount = null;
        private DLL.IBSU_CallbackFingerQuality m_callbackFingerQuality = null;
        private DLL.IBSU_CallbackDeviceCount m_callbackDeviceCount = null;
        private DLL.IBSU_CallbackInitProgress m_callbackInitProgress = null;
        private DLL.IBSU_CallbackTakingAcquisition m_callbackTakingAcquisition = null;
        private DLL.IBSU_CallbackCompleteAcquisition m_callbackCompleteAcquisition = null;
        private DLL.IBSU_CallbackClearPlatenAtCapture m_callbackClearPlaten = null;
        private DLL.IBSU_CallbackResultImageEx m_callbackResultImageEx = null;
        private DLL.IBSU_CallbackKeyButtons m_callbackPressedKeyButtons = null;


        private DLL.IBSU_SdkVersion m_verInfo;
        private int     m_nSelectedDevIndex;						///< Index of selected device
	    private int		m_nDevHandle;								///< Device handle
        public bool     m_bSelectDev;                                                            
        public bool     m_bInitializing;							///< Device initialization is in progress
        private int     m_nCurrentCaptureStep;
        private string  m_ImgSaveFolder;				            ///< Base folder for image saving
        private string  m_ImgSubFolder;								///< Sub Folder for image sequence
        private string  m_strImageMessage;
        private bool    m_bNeedClearPlaten;
        private bool    m_bBlank;
        private bool    m_bSaveWarningOfClearPlaten;
        private bool    m_bDevLocked;                         ///< Device Lock State
        private int     m_nOvImageTextHandle;
        private int     m_nOvClearPlatenHandle;
        private int[]   m_nOvSegmentHandle = new int[DLL.IBSU_MAX_SEGMENT_COUNT];
        private DLL.IBSU_LedType m_LedType;

        public DLL.IBSM_ImageData       m_CapturedImg;
        public DLL.IBSM_ImageData[]     m_CapturedImgSplit = new DLL.IBSM_ImageData[DLL.IBSU_MAX_SEGMENT_COUNT];
	    public int				        m_CapturedImgSplitCnt;


        private List<CaptureInfo> m_vecCaptureSeq = new List<CaptureInfo>();
        private DLL.IBSU_FingerQualityState[]	m_FingerQuality = new DLL.IBSU_FingerQualityState[DLL.IBSU_MAX_SEGMENT_COUNT];

        private string  m_CustomerKey = "";

        public SDKMainForm()
        {
            InitializeComponent();
        }


////////////////////////////////////////////////////////////////////////////////////////////
// User defined functions
        private bool _ChkFolder(string sPath)
        {
            DirectoryInfo di = new DirectoryInfo(sPath);

            return di.Exists;
        }

        private void _InitializeDeviceThreadCallback(object pParam)
        {
            if (pParam == null)
                return;

            ThreadParam param = (ThreadParam)pParam;
            IntPtr      formHandle = param.pParentHandle;
            IntPtr      frameImageHandle = param.pFrameImageHandle;
            int         devIndex = param.devIndex;
	        int			devHandle = -1;
	        int			nRc = DLL.IBSU_STATUS_OK;
            int         ledCount = 0;
            uint        operableLEDs = 0;
            StringBuilder minSDKVersion = new StringBuilder();
            StringBuilder errorString = new StringBuilder();

            m_bInitializing = true;
            nRc = DLL._IBSU_OpenDevice(devIndex, ref devHandle);
            m_bInitializing = false;

	        if( nRc >= DLL.IBSU_STATUS_OK )
	        {
		        m_nDevHandle = devHandle;

                DLL._IBSU_GetOperableLEDs(devHandle, ref m_LedType, ref ledCount, ref operableLEDs);
        		    
		        DLL.IBSU_RECT clientRect = new DLL.IBSU_RECT();
                Win32.GetClientRect(frameImageHandle, ref clientRect);

		        // Create display window
                DLL._IBSU_CreateClientWindow(devHandle, frameImageHandle, clientRect.left, clientRect.top, clientRect.right, clientRect.bottom);
                DLL._IBSU_AddOverlayQuadrangle(devHandle, ref m_nOvClearPlatenHandle, 0, 0, 0, 0, 0, 0, 0, 0, 0, (uint)0);
                DLL._IBSU_AddOverlayText(devHandle, ref m_nOvImageTextHandle, "Arial", 10, true, "", 10, 10, 0);

                for (int i = 0; i < DLL.IBSU_MAX_SEGMENT_COUNT; i++)
                {
                    DLL._IBSU_AddOverlayQuadrangle(devHandle, ref m_nOvSegmentHandle[i], 0, 0, 0, 0, 0, 0, 0, 0,
                    0, (uint)0);
                }

                /** Default value is 0x00d8e9ec( COLOR_BTNFACE ) for enumeration ENUM_IBSU_WINDOW_PROPERTY_BK_COLOR
                 ** You can change the background color as using method below
                                string cValue;
                                Color bkColor = SystemColors.ButtonFace;
                                cValue = String.Format("{0}", (uint)ColorTranslator.ToWin32(bkColor));
                                DLL._IBSU_SetClientDisplayProperty(devHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_BK_COLOR, cValue);
                */

                /** Default value is 0x0000FF (COLORREF:0xBBGGRR) for enumeration ENUM_IBSU_WINDOW_PROPERTY_ROLL_GUIDE_LINE_COLOR
                 ** You can change the Roll Guide Line color as using method below
                                StringBuilder cValue = new StringBuilder();
                                cValue.Append((int)0x0000FF);   // Red
                                DLL._IBSU_SetClientDisplayProperty( devHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_ROLL_GUIDE_LINE_COLOR, cValue );
                */

                /** Default value is TRUE for enumeration ENUM_IBSU_WINDOW_PROPERTY_ROLL_GUIDE_LINE
                 ** You can remove the guide line of rolling as using method below
                                cValue = "FALSE";
                                DLL._IBSU_SetClientDisplayProperty( devHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_ROLL_GUIDE_LINE, cValue );
                */

                // register callback functions
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_COMMUNICATION_BREAK, m_callbackDeviceCommunicationBreak, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_PREVIEW_IMAGE, m_callbackPreviewImage, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_TAKING_ACQUISITION, m_callbackTakingAcquisition, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_COMPLETE_ACQUISITION, m_callbackCompleteAcquisition, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_RESULT_IMAGE_EX, m_callbackResultImageEx, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_OPTIONAL_EVENT_FINGER_COUNT, m_callbackFingerCount, formHandle);
                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_OPTIONAL_EVENT_FINGER_QUALITY, m_callbackFingerQuality, formHandle);  
		        if( m_chkUseClearPlaten.Checked )
                    DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_OPTIONAL_EVENT_CLEAR_PLATEN_AT_CAPTURE, m_callbackClearPlaten, formHandle);

                DLL._IBSU_RegisterCallbacks(devHandle, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_KEYBUTTON, m_callbackPressedKeyButtons, formHandle);
            }

	        // status notification and sequence start
	        if( nRc == DLL.IBSU_STATUS_OK )
	        {
                OnMsg_CaptureSeqStart();
		        return;
	        }

	        if( nRc > DLL.IBSU_STATUS_OK )
                OnMsg_InitWarning();
	        else 
	        {
                string message;
		        switch (nRc)
		        {
		        case DLL.IBSU_ERR_DEVICE_ACTIVE:
                    message = String.Format("[Error code = {0}] Device initialization failed because in use by another thread/process.", nRc);
                    OnMsg_UpdateStatusMessage(message);
			        break;
		        case DLL.IBSU_ERR_USB20_REQUIRED:
                    message = String.Format("[Error code = {0}] Device initialization failed because SDK only works with USB 2.0.", nRc);
                    OnMsg_UpdateStatusMessage(message);
			        break;
                case DLL.IBSU_ERR_DEVICE_HIGHER_SDK_REQUIRED:
                    message = String.Format("[Error code = {0}] Device initialization failed because SDK only works with USB 2.0.", nRc);
                    DLL._IBSU_GetRequiredSDKVersion(devIndex, minSDKVersion);
                    message = String.Format("[Error code = {0}] Devcie initialization failed because SDK Version {1} is required at least.", nRc, minSDKVersion);
                    OnMsg_UpdateStatusMessage(message);
                    break;
                default:
                    DLL._IBSU_GetErrorString(nRc, errorString);
                    message = String.Format("[Error code = {0}] Device initialization failed. {1}", nRc, errorString);
                    OnMsg_UpdateStatusMessage(message);
			        break;
		        }
	        }

            OnMsg_UpdateDeviceList();
        }

        private void _SetStatusBarMessage(string message)
        {
            m_txtStatusMessage.Text = message;
        }

        private void _SetImageMessage(string message)
        {
	        int			font_size = 10;
	        int			x = 10;
	        int			y = 10;
	        Color	    cr = Color.FromArgb(0, 0, 255);

            if (m_bNeedClearPlaten)
            {
                cr = Color.FromArgb(255, 0, 0);
            }

            DLL._IBSU_ModifyOverlayText(m_nDevHandle, m_nOvImageTextHandle, "Arial", font_size, true, message, x, y, (uint)(ColorTranslator.ToWin32(cr))); 
            //DLL._IBSU_SetClientWindowOverlayText(m_nDevHandle, "Arial", font_size, true, message, x, y, (uint)ColorTranslator.ToWin32(cr));
        }

        private void _UpdateCaptureSequences()
        {
	        // store currently selected sequence
	        string strSelectedText="";
	        int selectedSeq = m_cboCaptureSeq.SelectedIndex;
            if (selectedSeq > -1)
                strSelectedText = m_cboCaptureSeq.Text;

	        // populate combo box
            m_cboCaptureSeq.Items.Clear();
	        m_cboCaptureSeq.Items.Add("- Please select -");

	        int devIndex = m_cboUsbDevices.SelectedIndex - 1;
	        DLL.IBSU_DeviceDesc devDesc = new DLL.IBSU_DeviceDesc();
	        if( devIndex > -1 )
		        DLL._IBSU_GetDeviceDescription( devIndex, ref devDesc );

	        if( ( devDesc.productName == "WATSON" ) ||
                ( devDesc.productName == "WATSON MINI" ) ||
                ( devDesc.productName == "SHERLOCK_ROIC" ) ||
                ( devDesc.productName == "SHERLOCK" ))
	        {
		        m_cboCaptureSeq.Items.Add( CAPTURE_SEQ_FLAT_SINGLE_FINGER );
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_ROLL_SINGLE_FINGER);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_2_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_SINGLE_ROLLED_FINGERS);
	        }
            else if ( ( devDesc.productName == "COLUMBO" ) ||
                      ( devDesc.productName == "CURVE" ) ||
                      (devDesc.productName == "COLUMBO MINI") ||
                      (devDesc.productName == "DANNO") ||
                      (devDesc.productName == "COLUMBO 2.0"))
            {
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_SINGLE_FINGER);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS);
            }
            else if ( ( devDesc.productName == "HOLMES" ) ||
                      (devDesc.productName == "KOJAK") ||
                      (devDesc.productName == "FIVE-0") ||
                      (devDesc.productName == "TF10") ||
                      (devDesc.productName == "MF10")) 
            {
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_SINGLE_FINGER);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_ROLL_SINGLE_FINGER);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_2_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_4_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_SINGLE_ROLLED_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_10_FLAT_WITH_4_FINGER_SCANNER);
            }
            else if ((devDesc.productName == "HALFPALM") ||
                     (devDesc.productName == "MANNIX"))
            {
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_ROLL_SINGLE_FINGER);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_2_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_4_FLAT_FINGERS);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_SINGLE_UPPER_HALFPALM);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_SINGLE_LOWER_HALFPALM);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_SINGLE_WRITERS_PALM);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_442);
                m_cboCaptureSeq.Items.Add(CAPTURE_SEQ_FLAT_TWO_HAND_HALFPALM);
            }

	        // select previously selected sequence
	        if( selectedSeq > -1 )
                selectedSeq = m_cboCaptureSeq.FindString(strSelectedText, 0);
            if (selectedSeq == -1)
                m_cboCaptureSeq.SelectedIndex = 0;
            else
                m_cboCaptureSeq.SelectedIndex = selectedSeq;

           	m_bDevLocked = devDesc.IsDeviceLocked;
            if (devIndex > -1 && m_bDevLocked)
            {
                lbLockStatus.Show();
                m_picLockStatus.Show();
            }
            else
            {
                lbLockStatus.Hide();
                m_picLockStatus.Hide();
            }

            OnMsg_UpdateDisplayResources();
        }

        private int _ReleaseDevice()
        {
	        int nRc = DLL.IBSU_STATUS_OK;
        	
	        if( m_nDevHandle != -1 )
		        nRc = DLL._IBSU_CloseDevice( m_nDevHandle );

	        if( nRc >= DLL.IBSU_STATUS_OK )
	        {
		        m_nDevHandle = -1;
		        m_nCurrentCaptureStep = -1;
		        m_bInitializing = false;
	        }

	        return nRc;
        }  

        private void _BeepFail()
        {
            DLL.IBSU_BeeperType beeperType = new DLL.IBSU_BeeperType();
            if (DLL._IBSU_GetOperableBeeper(m_nDevHandle, ref beeperType) != DLL.IBSU_STATUS_OK)
            {
                Win32.Beep(3500, 300);
                Thread.Sleep(150);
                Win32.Beep(3500, 150);
                Thread.Sleep(150);
                Win32.Beep(3500, 150);
                Thread.Sleep(150);
                Win32.Beep(3500, 150);
            }
            else
            {
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 12/*300ms = 12*25ms*/, 0, 0);
                Thread.Sleep(150);
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 6/*150ms = 6*25ms*/, 0, 0);
                Thread.Sleep(150);
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 6/*150ms = 6*25ms*/, 0, 0);
                Thread.Sleep(150);
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 6/*150ms = 6*25ms*/, 0, 0);
            }
        }

        private void _BeepSuccess()
        {
            DLL.IBSU_BeeperType beeperType = new DLL.IBSU_BeeperType();
            if (DLL._IBSU_GetOperableBeeper(m_nDevHandle, ref beeperType) != DLL.IBSU_STATUS_OK)
            {
                Win32.Beep(3500, 100);
                Thread.Sleep(50);
                Win32.Beep(3500, 100);
            }
            else
            {
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 4/*100ms = 4*25ms*/, 0, 0);
                Thread.Sleep(150);
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 4/*100ms = 4*25ms*/, 0, 0);
            }
        }

        private void _BeepOk()
        {
            DLL.IBSU_BeeperType beeperType = new DLL.IBSU_BeeperType();
            if (DLL._IBSU_GetOperableBeeper(m_nDevHandle, ref beeperType) != DLL.IBSU_STATUS_OK)
            {
                Win32.Beep(3500, 100);
            }
            else
            {
                DLL._IBSU_SetBeeper(m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 4/*100ms = 4*25ms*/, 0, 0);
            }
        }

        private void _BeepDeviceCommunicationBreak()
        {
	        for( int i=0; i<8; i++ )
	        {
                Win32.Beep(3500, 100);
                Thread.Sleep(100);
	        }
        }

        private void _SaveBitmapImage( ref DLL.IBSU_ImageData image, string fingerName ) 
        {
            if ((m_ImgSaveFolder == null) || (m_ImgSubFolder == null) ||
                (m_ImgSaveFolder.Length == 0) || (m_ImgSubFolder.Length == 0))
	        {
		        return;
	        }
          
	        string strFolder;
	        strFolder = String.Format( "{0}\\{1}", m_ImgSaveFolder, m_ImgSubFolder );
            System.IO.Directory.CreateDirectory(strFolder);

            string strFileName;
            strFileName = String.Format("{0}\\Image_{1}_{2}.bmp", strFolder, m_nCurrentCaptureStep, fingerName);

	        if( DLL._IBSU_SaveBitmapImage( strFileName, image.Buffer,
                                      image.Width, image.Height, image.Pitch, 
							          image.ResolutionX, image.ResolutionY ) != DLL.IBSU_STATUS_OK )
	        {
		        MessageBox.Show( "Failed to save bitmap image!");
	        }
        }

        private void _SaveWsqImage(ref DLL.IBSU_ImageData image, string fingerName)
        {
            if ((m_ImgSaveFolder == null) || (m_ImgSubFolder == null) ||
                (m_ImgSaveFolder.Length == 0) || (m_ImgSubFolder.Length == 0))
            {
                return;
            }

            string strFolder;
            strFolder = String.Format("{0}\\{1}", m_ImgSaveFolder, m_ImgSubFolder);
            System.IO.Directory.CreateDirectory(strFolder);

            string strFileName;
            strFileName = String.Format("{0}\\Image_{1}_{2}.wsq", strFolder, m_nCurrentCaptureStep, fingerName);

            // Bug Fixed, WSQ image was flipped vertically.
            // Pitch parameter is required to fix bug.
            if (DLL._IBSU_WSQEncodeToFile(strFileName, image.Buffer,
                                      (int)image.Width, (int)image.Height, image.Pitch, image.BitsPerPixel,
                                      (int)image.ResolutionX, 0.75, "") != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to save bitmap image!");
            }

            /***********************************************************
             * Example codes for WSQ encoding based on memory

            string filename;
            IntPtr pCompressedData = IntPtr.Zero;
            IntPtr pDecompressedData = IntPtr.Zero;
            IntPtr pDecompressedData2 = IntPtr.Zero;
	        int compressedLength=0;
	        if (DLL._IBSU_WSQEncodeMem(image.Buffer,
                                    (int)image.Width, (int)image.Height, image.Pitch, image.BitsPerPixel,
                                    (int)image.ResolutionX, (double)0.75, "",
                                    ref pCompressedData, ref compressedLength) != DLL.IBSU_STATUS_OK )
	        {
                MessageBox.Show("Failed to save WSQ_1 image!");
	        }

            byte [] compressedBuffer =new byte [compressedLength];
            Marshal.Copy(pCompressedData, compressedBuffer, 0, compressedLength);

            filename = String.Format("{0}\\Image_{1}_{2}_v1.wsq", strFolder, m_nCurrentCaptureStep, fingerName);
            FileStream fs = new FileStream(filename, FileMode.Create);
            BinaryWriter w = new BinaryWriter(fs);
            w.Write(compressedBuffer, 0, compressedLength);
            w.Close();

            int width=0, height=0, pitch=0, bitsPerPixel=0, pixelPerInch=0;
            if (DLL._IBSU_WSQDecodeMem(pCompressedData, compressedLength,
                                    ref pDecompressedData, ref width, ref height,
                                    ref pitch, ref bitsPerPixel, ref pixelPerInch) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to Decode WSQ image!");
            }

            filename = String.Format("{0}\\Image_{1}_{2}_v1.bmp", strFolder, m_nCurrentCaptureStep, fingerName);
            if (DLL._IBSU_SaveBitmapImage(filename, pDecompressedData,
                                      (uint)width, (uint)height, pitch,
                                      pixelPerInch, pixelPerInch) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to save bitmap v1 image!");
            }

            if (DLL._IBSU_WSQDecodeFromFile(strFileName, ref pDecompressedData2,
                                      ref width, ref height, ref pitch,
                                      ref pixelPerInch, ref pixelPerInch) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to Decode WSQ image!");
            }

            filename = String.Format("{0}\\Image_{1}_{2}_v2.bmp", strFolder, m_nCurrentCaptureStep, fingerName);
            if (DLL._IBSU_SaveBitmapImage(filename, pDecompressedData2,
                                      (uint)width, (uint)height, pitch,
                                      pixelPerInch, pixelPerInch) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to save bitmap v2 image!");
            }

            DLL._IBSU_FreeMemory(pCompressedData);
            DLL._IBSU_FreeMemory(pDecompressedData);
            DLL._IBSU_FreeMemory(pDecompressedData2);
            ***********************************************************/
        }

        private void _SavePngImage(ref DLL.IBSU_ImageData image, string fingerName)
        {
            if ((m_ImgSaveFolder == null) || (m_ImgSubFolder == null) ||
                (m_ImgSaveFolder.Length == 0) || (m_ImgSubFolder.Length == 0))
            {
                return;
            }

            string strFolder;
            strFolder = String.Format("{0}\\{1}", m_ImgSaveFolder, m_ImgSubFolder);
            System.IO.Directory.CreateDirectory(strFolder);

            string strFileName;
            strFileName = String.Format("{0}\\Image_{1}_{2}.png", strFolder, m_nCurrentCaptureStep, fingerName);

            if (DLL._IBSU_SavePngImage(strFileName, image.Buffer,
                                      image.Width, image.Height, image.Pitch,
                                      image.ResolutionX, image.ResolutionY) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to save png image!");
            }
        }

        private void _SaveJP2Image(ref DLL.IBSU_ImageData image, string fingerName)
        {
            if ((m_ImgSaveFolder == null) || (m_ImgSubFolder == null) ||
                (m_ImgSaveFolder.Length == 0) || (m_ImgSubFolder.Length == 0))
            {
                return;
            }

            string strFolder;
            strFolder = String.Format("{0}\\{1}", m_ImgSaveFolder, m_ImgSubFolder);
            System.IO.Directory.CreateDirectory(strFolder);

            string strFileName;
            strFileName = String.Format("{0}\\Image_{1}_{2}.jp2", strFolder, m_nCurrentCaptureStep, fingerName);

            if (DLL._IBSU_SaveJP2Image(strFileName, image.Buffer,
                                      image.Width, image.Height, image.Pitch,
                                      image.ResolutionX, image.ResolutionY, 80) != DLL.IBSU_STATUS_OK)
            {
                MessageBox.Show("Failed to save jpeg-2000 image!");
            }
        }


        private void _DrawRoundRect(Graphics g, Brush brush, float X, float Y, float width, float height, float radius)
        {
            GraphicsPath gp = new GraphicsPath();

            gp.AddLine(X + radius, Y, X + width - (radius * 2), Y);
            gp.AddArc(X + width - (radius * 2), Y, radius * 2, radius * 2, 270, 90);
            gp.AddLine(X + width, Y + radius, X + width, Y + height - (radius * 2));
            gp.AddArc(X + width - (radius * 2), Y + height - (radius * 2), radius * 2, radius * 2, 0, 90);
            gp.AddLine(X + width - (radius * 2), Y + height, X + radius, Y + height);
            gp.AddArc(X, Y + height - (radius * 2), radius * 2, radius * 2, 90, 90);
            gp.AddLine(X, Y + height - (radius * 2), X, Y + radius);
            gp.AddArc(X, Y, radius * 2, radius * 2, 180, 90);
            gp.CloseFigure();

//            g.DrawPath(p, gp);
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.FillPath(brush, gp);
            gp.Dispose();
        }

        private int _ModifyOverlayForWarningOfClearPlaten(Boolean bVisible)
        {
	        if( m_nDevHandle == -1 )
		        return -1;

            int      nRc = DLL.IBSU_STATUS_OK;
            Color	 cr = Color.FromArgb(255, 0, 0);
            int      left, top, right, bottom;

	        DLL.IBSU_RECT clientRect = new DLL.IBSU_RECT();
            Win32.GetClientRect(m_FrameImage.Handle, ref clientRect);

            left = 0; top = 0; right = clientRect.right - clientRect.left; bottom = clientRect.bottom - clientRect.top;
            if( bVisible )
	        {
		        nRc = DLL._IBSU_ModifyOverlayQuadrangle(m_nDevHandle, m_nOvClearPlatenHandle,
                    left, top, right, top, right, bottom, left, bottom, 20, (uint)(ColorTranslator.ToWin32(cr)));
	        }
	        else
	        {
		        nRc = DLL._IBSU_ModifyOverlayQuadrangle(m_nDevHandle, m_nOvClearPlatenHandle,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, (uint)0);
	        }

            return nRc;
        }

        private void _SetLEDs(int deviceHandle, CaptureInfo info, int ledColor, bool bBlink)
        {
	        uint setLEDs = 0;

            if (m_LedType == DLL.IBSU_LedType.ENUM_IBSU_LED_TYPE_FSCAN)
            {
                if (bBlink)
                {
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_BLINK_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_BLINK_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_BLINK_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_BLINK_RED;
                    }
                }

                if (info.ImageType == DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER)
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_ROLL;
                }

                if (info.fingerName == "SFF_Right_Thumb" ||
                    info.fingerName == "SRF_Right_Thumb")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_TWO_THUMB;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_RED;
                    }
                }
                else if (info.fingerName == "SFF_Left_Thumb" ||
                         info.fingerName == "SRF_Left_Thumb")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_TWO_THUMB;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_RED;
                    }
                }
                else if (info.fingerName == "TFF_2_Thumbs")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_TWO_THUMB;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_THUMB_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_THUMB_RED;
                    }
                }
                ///////////////////LEFT HAND////////////////////
                else if (info.fingerName == "SFF_Left_Index" ||
                         info.fingerName == "SRF_Left_Index")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_LEFT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_RED;
                    }
                }
                else if (info.fingerName == "SFF_Left_Middle" ||
                         info.fingerName == "SRF_Left_Middle")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_LEFT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_RED;
                    }
                }
                else if (info.fingerName == "SFF_Left_Ring" ||
                         info.fingerName == "SRF_Left_Ring")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_LEFT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_RED;
                    }
                }
                else if (info.fingerName == "SFF_Left_Little" ||
                         info.fingerName == "SRF_Left_Little")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_LEFT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_RED;
                    }
                }
                else if (info.fingerName == "4FF_Left_4_Fingers")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_LEFT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_INDEX_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_MIDDLE_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_RING_RED;
                        setLEDs |= DLL.IBSU_LED_F_LEFT_LITTLE_RED;
                    }
                }
                ///////////RIGHT HAND /////////////////////////
                else if (info.fingerName == "SFF_Right_Index" ||
                         info.fingerName == "SRF_Right_Index")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_RIGHT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_RED;
                    }
                }
                else if (info.fingerName == "SFF_Right_Middle" ||
                         info.fingerName == "SRF_Right_Middle")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_RIGHT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_RED;
                    }
                }
                else if (info.fingerName == "SFF_Right_Ring" ||
                         info.fingerName == "SRF_Right_Ring")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_RIGHT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_RED;
                    }
                }
                else if (info.fingerName == "SFF_Right_Little" ||
                         info.fingerName == "SRF_Right_Little")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_RIGHT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_RED;
                    }
                }
                else if (info.fingerName == "4FF_Right_4_Fingers")
                {
                    setLEDs |= DLL.IBSU_LED_F_PROGRESS_RIGHT_HAND;
                    if (ledColor == __LED_COLOR_GREEN__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_GREEN;
                    }
                    else if (ledColor == __LED_COLOR_RED__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_RED;
                    }
                    else if (ledColor == __LED_COLOR_YELLOW__)
                    {
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_GREEN;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_INDEX_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_MIDDLE_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_RING_RED;
                        setLEDs |= DLL.IBSU_LED_F_RIGHT_LITTLE_RED;
                    }
                }

                if (ledColor == __LED_COLOR_NONE__)
                {
                    setLEDs = 0;
                }

                DLL._IBSU_SetLEDs(deviceHandle, setLEDs);
            }
        }











        private static void OnEvent_DeviceCommunicationBreak(
            int         deviceIndex,
            IntPtr      pContext
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                pDlg.OnMsg_DeviceCommunicationBreak();
            }
        }

        private static void OnEvent_PreviewImage(
            int                 deviceHandle,
            IntPtr              pContext,
            DLL.IBSU_ImageData  image
            )
        {
            if (pContext == null)
                return;

            lock (SDKMainForm.m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
            }
        }

        private static void OnEvent_FingerCount(
            int                         deviceHandle,
            IntPtr                      pContext,
            DLL.IBSU_FingerCountState   fingerCountState
            )
        {
            if (pContext == null)
                return;

            lock (SDKMainForm.m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                if (deviceHandle != pDlg.m_nDevHandle)
                    return;
/*
                string fingerState;
                if (fingerCountState == DLL.IBSU_FingerCountState.ENUM_IBSU_FINGER_COUNT_OK)
                    fingerState = "FINGER_COUNT_OK";
                else if (fingerCountState == DLL.IBSU_FingerCountState.ENUM_IBSU_TOO_MANY_FINGERS)
                    fingerState = "TOO_MANY_FINGERS";
                else if (fingerCountState == DLL.IBSU_FingerCountState.ENUM_IBSU_TOO_FEW_FINGERS)
                    fingerState = "TOO_FEW_FINGERS";
                else if (fingerCountState == DLL.IBSU_FingerCountState.ENUM_IBSU_NON_FINGER)
                    fingerState = "NON-FINGER";
                else
                    fingerState = "UNKNOWN";
*/
                CaptureInfo info = pDlg.m_vecCaptureSeq[pDlg.m_nCurrentCaptureStep];

                if (fingerCountState == DLL.IBSU_FingerCountState.ENUM_IBSU_NON_FINGER)
                {
                    pDlg._SetLEDs(deviceHandle, info, __LED_COLOR_RED__, true);
                }
                else
                {
                    pDlg._SetLEDs(deviceHandle, info, __LED_COLOR_YELLOW__, true);
                }
            }
        }

        private static void OnEvent_FingerQuality(
            int         deviceHandle,
            IntPtr      pContext,
            IntPtr      pQualityArray,
            int         qualityArrayCount
            )
        {
            if (pContext == null)
                return;

            lock (SDKMainForm.m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                int[] qualityArray = new int[4];
                Marshal.Copy(pQualityArray, qualityArray, 0, qualityArrayCount);
                pDlg.m_FingerQuality[0] = (DLL.IBSU_FingerQualityState)qualityArray[0];
                pDlg.m_FingerQuality[1] = (DLL.IBSU_FingerQualityState)qualityArray[1];
                pDlg.m_FingerQuality[2] = (DLL.IBSU_FingerQualityState)qualityArray[2];
                pDlg.m_FingerQuality[3] = (DLL.IBSU_FingerQualityState)qualityArray[3];

                pDlg.m_picScanner.Invalidate(false);
            }
        }

        private static void OnEvent_DeviceCount(
            int     detectedDevices,
            IntPtr  pContext
            )
        {
            if (pContext == null)
                return;

            lock (SDKMainForm.m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                pDlg.OnMsg_UpdateDeviceList();
            }
        }

        private static void OnEvent_InitProgress(
            int     deviceIndex,
            IntPtr  pContext,
            int     progressValue
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                string message;
                message = String.Format("Initializing device... {0}%", progressValue);
                pDlg.OnMsg_UpdateStatusMessage(message);
            }
        }

        private static void OnEvent_TakingAcquisition(
            int                 deviceHandle,
            IntPtr              pContext,
            DLL.IBSU_ImageType  imageType
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                if (imageType == DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER)
                {
                    pDlg.OnMsg_Beep(__BEEP_OK__);
                    pDlg.m_strImageMessage = "When done remove finger from sensor";
                    pDlg.OnMsg_UpdateImageMessage(pDlg.m_strImageMessage);
                    pDlg.OnMsg_UpdateStatusMessage(pDlg.m_strImageMessage);
                }
            }
        }

        private static void OnEvent_CompleteAcquisition(
            int                 deviceHandle,
            IntPtr              pContext,
            DLL.IBSU_ImageType  imageType
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                if (imageType == DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER)
                {
                    pDlg.OnMsg_Beep(__BEEP_OK__);
                }
                else
                {
                    pDlg.OnMsg_Beep(__BEEP_SUCCESS__);
                    pDlg.m_strImageMessage = "Remove fingers from sensor";
                    pDlg.OnMsg_UpdateImageMessage(pDlg.m_strImageMessage);
                    pDlg.m_strImageMessage = "Acquisition completed, postprocessing..";
                    pDlg.OnMsg_UpdateStatusMessage(pDlg.m_strImageMessage);
                    DLL._IBSU_RedrawClientWindow(deviceHandle);
                }
            }
        }

		/****
		 ** This IBSU_CallbackResultImage callback was deprecated since 1.7.0
		 ** Please use IBSU_CallbackResultImageEx instead
		*/
        private static void OnEvent_ResultImageEx(int deviceHandle, IntPtr pContext, int imageStatus, DLL.IBSU_ImageData image, DLL.IBSU_ImageType imageType, int detectedFingerCount, int segmentImageArrayCount, IntPtr pSegmentImageArray, IntPtr pSegmentPositionArray)
        {
            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                if (deviceHandle != pDlg.m_nDevHandle)
                {
                    return;
                }

                if (imageStatus >= DLL.IBSU_STATUS_OK)
                {
                    if (imageType == DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER)
                    {
                        pDlg.OnMsg_Beep(__BEEP_SUCCESS__);
                    }
                }

                // Added 2012-11-30
                if (pDlg.m_bNeedClearPlaten)
                {
                    pDlg.m_bNeedClearPlaten = false;
                    pDlg.m_picScanner.Invalidate();
                }

                // Image acquisition successful
                string imgTypeName = null;

                switch (imageType)
                {
                    case DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER:
                        imgTypeName = "-- Rolling single finger --";
                        break;
                    case DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_FINGER:
                        imgTypeName = "-- Flat single finger --";
                        break;
                    case DLL.IBSU_ImageType.ENUM_IBSU_FLAT_TWO_FINGERS:
                        imgTypeName = "-- Flat two fingers --";
                        break;
                    case DLL.IBSU_ImageType.ENUM_IBSU_FLAT_FOUR_FINGERS:
                        imgTypeName = "-- Flat 4 fingers --";
                        break;
                    default:
                        imgTypeName = "-- Unknown --";
                        break;
                }

                int i = 0;

                if (imageStatus >= DLL.IBSU_STATUS_OK)
                {
                    CaptureInfo info = pDlg.m_vecCaptureSeq[pDlg.m_nCurrentCaptureStep];
                    pDlg._SetLEDs(deviceHandle, info, __LED_COLOR_GREEN__, false);

                    if (pDlg.m_chkSaveImages.Checked)
                    {
                        pDlg.OnMsg_UpdateStatusMessage("Saving image...");
                        info = pDlg.m_vecCaptureSeq[pDlg.m_nCurrentCaptureStep];
                        pDlg._SaveBitmapImage(ref image, info.fingerName);
                        pDlg._SaveWsqImage(ref image, info.fingerName);
                        pDlg._SavePngImage(ref image, info.fingerName);
                        pDlg._SaveJP2Image(ref image, info.fingerName);
                        if (segmentImageArrayCount > 0)
                        {
                            DLL.IBSU_ImageData[] imageArray = new DLL.IBSU_ImageData[segmentImageArrayCount];
                            string segmentName = null;
                            IntPtr ptrRunner = pSegmentImageArray;
                            for (i = 0; i < segmentImageArrayCount; i++)
                            {
                                segmentName = String.Format("{0}_Segement_{1}", info.fingerName, i);
                                imageArray[i] = (DLL.IBSU_ImageData)Marshal.PtrToStructure(ptrRunner, typeof(DLL.IBSU_ImageData));
                                pDlg._SaveBitmapImage(ref imageArray[i], segmentName);
                                pDlg._SaveWsqImage(ref imageArray[i], segmentName);
                                pDlg._SavePngImage(ref imageArray[i], segmentName);
                                pDlg._SaveJP2Image(ref imageArray[i], segmentName);
                                ptrRunner = (IntPtr)((long)ptrRunner + Marshal.SizeOf(imageArray[0]));
                            }
                        }

                    }

                    if (pDlg.m_chkDrawSegmentImage.Checked)
                    {
                        StringBuilder propertyValue = new StringBuilder();
                        double scaleFactor = 0;
                        int leftMargin = 0;
                        int TopMargin = 0;

                        DLL._IBSU_GetClientWindowProperty(deviceHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_SCALE_FACTOR, propertyValue);
                        scaleFactor = double.Parse(propertyValue.ToString());
                        DLL._IBSU_GetClientWindowProperty(deviceHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_LEFT_MARGIN, propertyValue);
                        leftMargin = int.Parse(propertyValue.ToString());
                        DLL._IBSU_GetClientWindowProperty(deviceHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_TOP_MARGIN, propertyValue);
                        TopMargin = int.Parse(propertyValue.ToString());

                        DLL.IBSU_SegmentPosition[] segmentArray = new DLL.IBSU_SegmentPosition[DLL.IBSU_MAX_SEGMENT_COUNT];
                        IntPtr ptrRunner_segmentArray = pSegmentPositionArray;

                        for (i = 0; i < segmentImageArrayCount; i++)
                        {
                            Color cr = Color.FromArgb(0, 128, 0);
                            int x1 = 0;
                            int x2 = 0;
                            int x3 = 0;
                            int x4 = 0;

                            int y1 = 0;
                            int y2 = 0;
                            int y3 = 0;
                            int y4 = 0;

                            segmentArray[i] = (DLL.IBSU_SegmentPosition)Marshal.PtrToStructure(ptrRunner_segmentArray, typeof(DLL.IBSU_SegmentPosition));

                            x1 = leftMargin + (int)(segmentArray[i].x1 * scaleFactor);
                            x2 = leftMargin + (int)(segmentArray[i].x2 * scaleFactor);
                            x3 = leftMargin + (int)(segmentArray[i].x3 * scaleFactor);
                            x4 = leftMargin + (int)(segmentArray[i].x4 * scaleFactor);

                            y1 = TopMargin + (int)(segmentArray[i].y1 * scaleFactor);
                            y2 = TopMargin + (int)(segmentArray[i].y2 * scaleFactor);
                            y3 = TopMargin + (int)(segmentArray[i].y3 * scaleFactor);
                            y4 = TopMargin + (int)(segmentArray[i].y4 * scaleFactor);

                            DLL._IBSU_ModifyOverlayQuadrangle(deviceHandle, pDlg.m_nOvSegmentHandle[i], x1, y1, x2, y2, x3, y3, x4, y4, 1, Convert.ToUInt32(ColorTranslator.ToWin32(cr)));
                            ptrRunner_segmentArray = (IntPtr)((long)ptrRunner_segmentArray + Marshal.SizeOf(segmentArray[0]));


                        }
                    }

                    if (pDlg.m_chkNFIQScore.Checked)
                    {
                        int[] nfiq_score = new int[DLL.IBSU_MAX_SEGMENT_COUNT + 1];
                        int score = 0;
                        int nRc = 0;
                        int segment_pos = 0;
                        DLL.IBSU_ImageData[] imageArray = new DLL.IBSU_ImageData[DLL.IBSU_MAX_SEGMENT_COUNT];
                        IntPtr ptrRunner = pSegmentImageArray;

                        for (i = 0; i <= DLL.IBSU_MAX_SEGMENT_COUNT; i++)
                        {
                            nfiq_score[i] = 0;
                        }

                        string strValue = "Err";
                        pDlg.OnMsg_UpdateStatusMessage("Get NFIQ score...");

                        for (i = 0; i < DLL.IBSU_MAX_SEGMENT_COUNT; i++)
                        {
                            if (pDlg.m_FingerQuality[i] == DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT)
                            {
                                continue;
                            }
                            imageArray[i] = (DLL.IBSU_ImageData)Marshal.PtrToStructure(ptrRunner, typeof(DLL.IBSU_ImageData));

                            nRc = DLL._IBSU_GetNFIQScore(deviceHandle, imageArray[i].Buffer, imageArray[i].Width, imageArray[i].Height, imageArray[i].BitsPerPixel, ref score);

                            if (nRc == DLL.IBSU_STATUS_OK)
                            {
                                nfiq_score[i] = score;
                            }
                            else
                            {
                                nfiq_score[i] = -1;
                            }

                            segment_pos = segment_pos + 1;
                            ptrRunner = (IntPtr)((long)ptrRunner + Marshal.SizeOf(imageArray[0]));
                        }
                        strValue = String.Format("{0}-{1}-{2}-{3}", nfiq_score[0], nfiq_score[1], nfiq_score[2], nfiq_score[3]);
                        pDlg.OnMsg_UpdateNFIQScore(strValue);
                    }

                    if (pDlg.m_chkEnableSpoof.Checked)
                    {
                        DLL.IBSU_ImageData[] imageArray = new DLL.IBSU_ImageData[DLL.IBSU_MAX_SEGMENT_COUNT];
                        IntPtr ptrRunner = pSegmentImageArray;
                        int nRc = 0;
                        bool IsSpoof = false;
                        String[] isSpoofStr = new String[4];

                        pDlg.OnMsg_UpdateStatusMessage("Get Spoof result...");

                        for (i = 0; i < segmentImageArrayCount; i++)
                        {
                            imageArray[i] = (DLL.IBSU_ImageData)Marshal.PtrToStructure(ptrRunner, typeof(DLL.IBSU_ImageData));
                            nRc = DLL._IBSU_IsSpoofFingerDetected(deviceHandle, imageArray[i], ref IsSpoof);
                            if(nRc != DLL.IBSU_STATUS_OK)
                            {
                                pDlg.OnMsg_UpdateSpoofResult("Error");

                                StringBuilder errString = new StringBuilder();
                                DLL._IBSU_GetErrorString(nRc, errString);

                                string strValue = null;
                                strValue = String.Format("{0} (Error code = {1})", errString, nRc);
                                pDlg._SetImageMessage(strValue);
                                pDlg.OnMsg_UpdateStatusMessage(strValue);

                                pDlg.OnMsg_CaptureSeqNext();
			                    return;
                            }

                            if (IsSpoof == true)
                                isSpoofStr[i] = "FAKE";
                            else
                                isSpoofStr[i] = "LIVE";

                            ptrRunner = (IntPtr)((long)ptrRunner + Marshal.SizeOf(imageArray[0]));
                        }

                        string spoofResultStr = "";

                        for (int j = 0; j < segmentImageArrayCount; ++j)
                        {
                            if (j > 0)
                                spoofResultStr += "-";
                            spoofResultStr += isSpoofStr[j];
                        }

                        pDlg.OnMsg_UpdateSpoofResult(spoofResultStr);

                    }

                    string strValue1 = null;
                    if (imageStatus == DLL.IBSU_STATUS_OK)
                    {
                        strValue1 = String.Format("{0} acquisition completed successfully", imgTypeName);
                        pDlg._SetImageMessage(strValue1);
                        pDlg.OnMsg_UpdateStatusMessage(strValue1);
                    }
                    else
                    {
                        strValue1 = String.Format("{0} acquisition Waring (Warning code = {1})", imgTypeName, imageStatus);
                        pDlg._SetImageMessage(strValue1);
                        pDlg.OnMsg_UpdateStatusMessage(strValue1);

                        pDlg.OnMsg_AskRecapture(imageStatus);
                        return;
                    }
                }
                else
                {
                    pDlg.m_strImageMessage = String.Format("{0} acquisition fail (Error code = {1})", imgTypeName, imageStatus);
                    pDlg._SetImageMessage(pDlg.m_strImageMessage);
                    pDlg.OnMsg_UpdateStatusMessage(pDlg.m_strImageMessage);
                    pDlg.m_nCurrentCaptureStep = pDlg.m_vecCaptureSeq.Count;

                }
                pDlg.OnMsg_CaptureSeqNext();
            }

        }



        private static void OnEvent_ClearPlatenAtCapture(
            int                     deviceIndex,
            IntPtr                  pContext,
            DLL.IBSU_PlatenState    platenState
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                if (platenState == DLL.IBSU_PlatenState.ENUM_IBSU_PLATEN_HAS_FINGERS)
                    pDlg.m_bNeedClearPlaten = true;
                else
                    pDlg.m_bNeedClearPlaten = false;

                if (pDlg.m_bNeedClearPlaten)
                {
                    pDlg.m_strImageMessage = "Please remove your fingers on the platen first!";
                    pDlg._SetImageMessage(pDlg.m_strImageMessage);
                    pDlg.OnMsg_UpdateStatusMessage(pDlg.m_strImageMessage);
                }
                else
                {
                    CaptureInfo info = pDlg.m_vecCaptureSeq[pDlg.m_nCurrentCaptureStep];

                    // Display message for image acuisition again
                    string strMessage;
                    strMessage = String.Format("{0}", info.PreCaptureMessage);

                    pDlg.OnMsg_UpdateStatusMessage(strMessage);
                    if (!pDlg.m_chkAutoCapture.Checked)
                        strMessage += String.Format("\r\nPress button 'Take Result Image' when image is good!");

                    pDlg._SetImageMessage(strMessage);
                    pDlg.m_strImageMessage = strMessage;
                }

                pDlg.m_picScanner.Invalidate(false);
            }
        }

        private static void OnEvent_PressedKeyButtons(
            int deviceIndex,
            IntPtr pContext,
            int pressedKeyButtons
            )
        {
            if (pContext == null)
                return;

            lock (m_sync)
            {
                SDKMainForm pDlg = (SDKMainForm)SDKMainForm.FromHandle(pContext);
                string message;
                message = String.Format("OnEvent_PressedKeyButtons = {0}", pressedKeyButtons);
                pDlg.OnMsg_UpdateStatusMessage(message);

                pDlg.OnMsg_GetSelectDevice();
                bool idle = !pDlg.m_bInitializing && (pDlg.m_nCurrentCaptureStep == -1);
                bool active = !pDlg.m_bInitializing && (pDlg.m_nCurrentCaptureStep != -1);                

                if (pressedKeyButtons == __LEFT_KEY_BUTTON__)
                {
                    if (pDlg.m_bSelectDev && idle)
                    {
                        DLL._IBSU_SetBeeper(pDlg.m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 4/*100ms = 4*25ms*/, 0, 0);
                        pDlg.OnMsg_CaptureStartClick();
                    }
                }
                else if (pressedKeyButtons == __RIGHT_KEY_BUTTON__)
                {
                    if ((active))
                    {
                        DLL._IBSU_SetBeeper(pDlg.m_nDevHandle, DLL.IBSU_BeepPattern.ENUM_IBSU_BEEP_PATTERN_GENERIC, 2/*Sol*/, 4/*100ms = 4*25ms*/, 0, 0);
                        pDlg.OnMsg_CaptureStopClick();
                    }
                }
            }
        }




        private delegate void OnMsg_GetSelectDeviceDelegate();
        private void OnMsg_GetSelectDevice()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.Invoke(new OnMsg_GetSelectDeviceDelegate(OnMsg_GetSelectDevice));

                return;
            }

            m_bSelectDev = m_cboUsbDevices.SelectedIndex > 0;

            return;
        }



        private delegate void OnMsg_CaptureStartClickDelegate();
        private void OnMsg_CaptureStartClick()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_CaptureStartClickDelegate(OnMsg_CaptureStartClick));

                return;
            }

            if (m_bInitializing)
                return;

            int devIndex = m_cboUsbDevices.SelectedIndex - 1;
            if (devIndex < 0)
                return;

            if (m_nCurrentCaptureStep != -1)
            {
                bool IsActive = false;
                int nRc;
                nRc = DLL._IBSU_IsCaptureActive(m_nDevHandle, ref IsActive);
                if (nRc == DLL.IBSU_STATUS_OK && IsActive)
                {
                    DLL._IBSU_TakeResultImageManually(m_nDevHandle);
                }

                return;
            }

            if (m_nDevHandle == -1)
            {
                m_bInitializing = true;

                if (m_bDevLocked)
                {
                    if (InputBox("Input Box", "Enter Customer Key", ref m_CustomerKey) == DialogResult.OK)
                    {
                        // Set Customer Key
                        int nRc = DLL._IBSU_SetCustomerKey(devIndex, DLL.IBSU_HashType.ENUM_IBSU_HASH_TYPE_SHA256, m_CustomerKey);//m_CustomerKey);
                        if (nRc != DLL.IBSU_STATUS_OK)
                        {
                            StringBuilder errorString = new StringBuilder();
                            DLL._IBSU_GetErrorString(nRc, errorString);
                            _SetStatusBarMessage(errorString.ToString());
                            return;
                        }
                    }
                }

                m_initThread = new Thread(new ParameterizedThreadStart(_InitializeDeviceThreadCallback));
                ThreadParam param = new ThreadParam();
                param.devIndex = devIndex;
                param.pParentHandle = this.Handle;
                param.pFrameImageHandle = m_FrameImage.Handle;
                m_initThread.Start(param);
            }
            else
            {
                // device already initialized
                OnMsg_CaptureSeqStart();
            }

            OnMsg_UpdateDisplayResources();
        }



        private delegate void OnMsg_CaptureStopClickDelegate();
        private void OnMsg_CaptureStopClick()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_CaptureStopClickDelegate(OnMsg_CaptureStopClick));

                return;
            }

            if (m_nDevHandle == -1)
                return;

            DLL._IBSU_CancelCaptureImage(m_nDevHandle);
            CaptureInfo m_tmpInfo = new CaptureInfo();
            _SetLEDs(m_nDevHandle, m_tmpInfo, __LED_COLOR_NONE__, false);
            m_nCurrentCaptureStep = -1;
            m_bNeedClearPlaten = false;

            string message;
            message = String.Format("Capture Sequence aborted");
            _SetStatusBarMessage(message);
            m_strImageMessage = "";
            _SetImageMessage("");
            OnMsg_UpdateDisplayResources();
        }



        private delegate void OnMsg_CaptureSeqStartDelegate();
        private void OnMsg_CaptureSeqStart()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_CaptureSeqStartDelegate(OnMsg_CaptureSeqStart));

                return;
            }

            if (m_nDevHandle == -1)
            {
                OnMsg_UpdateDisplayResources();
                return;
            }

            string strCaptureSeq="";
            int nSelectedSeq;
            nSelectedSeq = m_cboCaptureSeq.SelectedIndex;
            if (nSelectedSeq > -1)
                strCaptureSeq = m_cboCaptureSeq.Text;

            m_vecCaptureSeq.Clear();
            CaptureInfo info = new CaptureInfo();

            /** Please refer to definition below
            private const string CAPTURE_SEQ_FLAT_SINGLE_FINGER	= "Single flat finger";
            private const string CAPTURE_SEQ_ROLL_SINGLE_FINGER = "Single rolled finger";
            private const string CAPTURE_SEQ_2_FLAT_FINGERS = "2 flat fingers";
            private const string CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS = "10 single flat fingers";
            private const string CAPTURE_SEQ_10_SINGLE_ROLLED_FINGERS = "10 single rolled fingers";
            */
            if (strCaptureSeq == CAPTURE_SEQ_FLAT_SINGLE_FINGER)
            {
                info.PreCaptureMessage = "Please put a single finger on the sensor!";
                info.PostCaptuerMessage = "Keep finger on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_FINGER;
                info.NumberOfFinger = 1;
                info.fingerName = "SFF_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
                int count = m_vecCaptureSeq.Count;
            }

            if (strCaptureSeq == CAPTURE_SEQ_ROLL_SINGLE_FINGER)
            {
                info.PreCaptureMessage = "Please put a single finger on the sensor!";
                info.PostCaptuerMessage = "Roll finger!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER;
                info.NumberOfFinger = 1;
                info.fingerName = "SRF_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_2_FLAT_FINGERS)
            {
                info.PreCaptureMessage = "Please put two fingers on the sensor!";
                info.PostCaptuerMessage = "Keep fingers on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_TWO_FINGERS;
                info.NumberOfFinger = 2;
                info.fingerName = "TFF_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_10_SINGLE_FLAT_FINGERS)
            {
                info.PreCaptureMessage = "Please put right thumb on the sensor!";
                info.fingerName = "SFF_Right_Thumb";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_THUMB;
                info.PostCaptuerMessage = "Keep fingers on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_FINGER;
                info.NumberOfFinger = 1;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right index on the sensor!";
                info.fingerName = "SFF_Right_Index";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_INDEX_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right middle on the sensor!";
                info.fingerName = "SFF_Right_Middle";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_MIDDLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right ring on the sensor!";
                info.fingerName = "SFF_Right_Ring";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_RING_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right little on the sensor!";
                info.fingerName = "SFF_Right_Little";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_LITTLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left thumb on the sensor!";
                info.fingerName = "SFF_Left_Thumb";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_THUMB;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left index on the sensor!";
                info.fingerName = "SFF_Left_Index";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_INDEX_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left middle on the sensor!";
                info.fingerName = "SFF_Left_Middle";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_MIDDLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left ring on the sensor!";
                info.fingerName = "SFF_Left_Ring";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_RING_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left little on the sensor!";
                info.fingerName = "SFF_Left_Little";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_LITTLE_FINGER;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_10_SINGLE_ROLLED_FINGERS)
            {
                info.PreCaptureMessage = "Please put right thumb on the sensor!";
                info.PostCaptuerMessage = "Roll finger!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_ROLL_SINGLE_FINGER;
                info.NumberOfFinger = 1;
                info.fingerName = "SRF_Right_Thumb";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_THUMB;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right index on the sensor!";
                info.fingerName = "SRF_Right_Index";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_INDEX_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right middle on the sensor!";
                info.fingerName = "SRF_Right_Middle";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_MIDDLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right ring on the sensor!";
                info.fingerName = "SRF_Right_Ring";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_RING_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right little on the sensor!";
                info.fingerName = "SRF_Right_Little";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_LITTLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left thumb on the sensor!";
                info.fingerName = "SRF_Left_Thumb";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_THUMB;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left index on the sensor!";
                info.fingerName = "SRF_Left_Index";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_INDEX_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left middle on the sensor!";
                info.fingerName = "SRF_Left_Middle";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_MIDDLE_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left ring on the sensor!";
                info.fingerName = "SRF_Left_Ring";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_RING_FINGER;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left little on the sensor!";
                info.fingerName = "SRF_Left_Little";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_LITTLE_FINGER;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_4_FLAT_FINGERS)
            {
                info.PreCaptureMessage = "Please put 4 fingers on the sensor!";
                info.PostCaptuerMessage = "Keep fingers on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_FOUR_FINGERS;
                info.NumberOfFinger = 4;
                info.fingerName = "4FF_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_10_FLAT_WITH_4_FINGER_SCANNER)
            {
                info.PreCaptureMessage = "Please put right 4-fingers on the sensor!";
                info.fingerName = "4FF_Right_4_Fingers";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_RIGHT_FOUR_FINGERS;
                info.PostCaptuerMessage = "Keep fingers on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_FOUR_FINGERS;
                info.NumberOfFinger = 4;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left 4-fingers on the sensor!";
                info.fingerName = "4FF_Left_4_Fingers";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_LEFT_FOUR_FINGERS;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put 2-thumbs on the sensor!";
                info.fingerName = "TFF_2_Thumbs";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_THUMBS;
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_TWO_FINGERS;
                info.NumberOfFinger = 2;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_FLAT_SINGLE_WRITERS_PALM)
            {
                info.PreCaptureMessage = "Please put a single writer's palm on the sensor!";
                info.PostCaptuerMessage = "Flat Writer's palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_WRITERS_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_FLAT_SINGLE_UPPER_HALFPALM)
            {
                info.PreCaptureMessage = "Please put a upper palm on the sensor!";
                info.PostCaptuerMessage = "Flat upper palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_UPPER_PALM;
                info.NumberOfFinger = 5;
                info.fingerName = "5FP_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_FLAT_SINGLE_LOWER_HALFPALM)
            {
                info.PreCaptureMessage = "Please put a lower palm on the sensor!";
                info.PostCaptuerMessage = "Flat lower palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_LOWER_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Unknown";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_UNKNOWN;
                m_vecCaptureSeq.Add(info);
            }

            if (strCaptureSeq == CAPTURE_SEQ_FLAT_442)
            {
                // [Start] 4-4-2
                info.PreCaptureMessage = "Please put right 4-fingers on the sensor!";
                info.fingerName = "4FF_Right_4_Fingers";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_RIGHT_FOUR_FINGERS;
                info.PostCaptuerMessage = "Keep fingers on the sensor!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_FOUR_FINGERS;
                info.NumberOfFinger = 4;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left 4-fingers on the sensor!";
                info.fingerName = "4FF_Left_4_Fingers";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_LEFT_FOUR_FINGERS;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put 2-thumbs on the sensor!";
                info.fingerName = "TFF_2_Thumbs";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_PLAIN_THUMBS;
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_TWO_FINGERS;
                info.NumberOfFinger = 2;
                m_vecCaptureSeq.Add(info);
                // [End] 4-4-2
            }

            if(strCaptureSeq == CAPTURE_SEQ_FLAT_TWO_HAND_HALFPALM)
            {
                // [START] Right Half-palm
                info.PreCaptureMessage = "Please put right upper palm on the sensor!";
                info.PostCaptuerMessage = "Flat right upper palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_UPPER_PALM;
                info.NumberOfFinger = 5;
                info.fingerName = "5FP_Right_Upper_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_UPPER_HALF_PALM;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right lower palm on the sensor!";
                info.PostCaptuerMessage = "Flat right lower palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_LOWER_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Right_Lower_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_LOWER_HALF_PALM;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put right writer's palm on the sensor!";
                info.PostCaptuerMessage = "Flat right writer's palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_WRITERS_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Right_Writers_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_RIGHT_WRITERS_PALM;
                m_vecCaptureSeq.Add(info);
                // [END] Right Half-palm

                // [START] Left Half-palm
                info.PreCaptureMessage = "Please put left upper palm on the sensor!";
                info.PostCaptuerMessage = "Flat left upper palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_UPPER_PALM;
                info.NumberOfFinger = 5;
                info.fingerName = "5FP_Left_Upper_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_UPPER_HALF_PALM;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left lower palm on the sensor!";
                info.PostCaptuerMessage = "Flat left lower palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_LOWER_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Left_Lower_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_LOWER_HALF_PALM;
                m_vecCaptureSeq.Add(info);

                info.PreCaptureMessage = "Please put left writer's palm on the sensor!";
                info.PostCaptuerMessage = "Flat left writer's palm!";
                info.ImageType = DLL.IBSU_ImageType.ENUM_IBSU_FLAT_SINGLE_WRITERS_PALM;
                info.NumberOfFinger = 1;
                info.fingerName = "SFP_Left_Writers_Palm";
                info.fingerPosition = DLL.IBSM_FingerPosition.IBSM_FINGER_POSITION_LEFT_WRITERS_PALM;
                m_vecCaptureSeq.Add(info);
                // [END] Left Half-palm
            }

            // Make subfolder name
            m_ImgSubFolder = DateTime.Now.ToString("yyyy-MM-dd HHmmss");

            OnMsg_CaptureSeqNext();
        }

        private delegate void OnMsg_CaptureSeqNextDelegate();
        private void OnMsg_CaptureSeqNext()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_CaptureSeqNextDelegate(OnMsg_CaptureSeqNext));

                return;
            }

            int nRc;

            if (m_nDevHandle == -1)
                return;

            m_bBlank = false;
            m_FingerQuality[0] = DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT;
            m_FingerQuality[1] = DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT;
            m_FingerQuality[2] = DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT;
            m_FingerQuality[3] = DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT;


            m_nCurrentCaptureStep++;
            if (m_nCurrentCaptureStep >= m_vecCaptureSeq.Count)
            {
                // All of capture sequence completely
                CaptureInfo m_tmpInfo = new CaptureInfo();
                _SetLEDs(m_nDevHandle, m_tmpInfo, __LED_COLOR_NONE__, false);
                m_nCurrentCaptureStep = -1;
                m_ImgSubFolder = "";

                OnMsg_UpdateDisplayResources();
                Win32.SetFocus(m_btnCaptureStart.Handle);
                return;
            }

	        if( m_chkInvalidArea.Checked )
	        {
                StringBuilder propertyValue = new StringBuilder("TRUE");
                DLL._IBSU_SetClientDisplayProperty(m_nDevHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_DISP_INVALID_AREA, propertyValue);
	        }
	        else
	        {
                StringBuilder propertyValue = new StringBuilder("FALSE");
                DLL._IBSU_SetClientDisplayProperty(m_nDevHandle, DLL.IBSU_ClientWindowPropertyId.ENUM_IBSU_WINDOW_PROPERTY_DISP_INVALID_AREA, propertyValue);
	        }

            if (m_chkDetectSmear.Checked)
            {
                StringBuilder propertyValue = new StringBuilder("1");
                DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_ROLL_MODE, propertyValue);
                StringBuilder strValue = new StringBuilder();
                strValue.Append(m_cboSmearLevel.GetItemText(m_cboSmearLevel.SelectedIndex));
                DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_ROLL_LEVEL, strValue);
            }
            else
            {
                StringBuilder propertyValue = new StringBuilder("0");
                DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_ROLL_MODE, propertyValue);
            }

            OnMsg_UpdateSpoofResult("");
            if (m_chkEnableSpoof.Checked)
            {
                StringBuilder propertyValue = new StringBuilder("TRUE");
                nRc = DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_ENABLE_SPOOF, propertyValue);
                // Disable segment rotation for the better PAD perfomance
                nRc = DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_DISABLE_SEGMENT_ROTATION, propertyValue);

                if (nRc == DLL.IBSU_STATUS_OK)
                {
                    StringBuilder strValue = new StringBuilder();
                    strValue.Append(m_cboSpoofLevel.GetItemText(m_cboSpoofLevel.SelectedItem));
                    DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_SPOOF_LEVEL, strValue);
                }
       
            }
            else
            {
                StringBuilder propertyValue = new StringBuilder("FALSE");
                DLL._IBSU_SetProperty(m_nDevHandle, DLL.IBSU_PropertyId.ENUM_IBSU_PROPERTY_ENABLE_SPOOF, propertyValue);
            }

            for (int i = 0; i < DLL.IBSU_MAX_SEGMENT_COUNT; i++)
            {
                DLL._IBSU_ModifyOverlayQuadrangle(m_nDevHandle, m_nOvSegmentHandle[i], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
            }

            // Make capture delay for display result image on multi capture mode (500 ms)
            if (m_nCurrentCaptureStep > 0)
            {
                Thread.Sleep(500);
                m_strImageMessage = "";
            }

            CaptureInfo info = m_vecCaptureSeq[m_nCurrentCaptureStep];

            DLL.IBSU_ImageResolution imgRes = DLL.IBSU_ImageResolution.ENUM_IBSU_IMAGE_RESOLUTION_500;
            bool bAvailable = false;
            nRc = DLL._IBSU_IsCaptureAvailable(m_nDevHandle, info.ImageType, imgRes, ref bAvailable);
            if (nRc != DLL.IBSU_STATUS_OK || !bAvailable)
            {
                string message;
                message = String.Format("The capture mode {0} is not available", info.ImageType);
                _SetStatusBarMessage(message);
                m_nCurrentCaptureStep = -1;
                OnMsg_UpdateDisplayResources();
                return;
            }

            // Start capture
            uint captureOptions = 0;
            if (m_chkAutoContrast.Checked)
                captureOptions |= DLL.IBSU_OPTION_AUTO_CONTRAST;
            if (m_chkAutoCapture.Checked)
                captureOptions |= DLL.IBSU_OPTION_AUTO_CAPTURE;
            if (m_chkIgnoreFingerCount.Checked)
                captureOptions |= DLL.IBSU_OPTION_IGNORE_FINGER_COUNT;

            nRc = DLL._IBSU_BeginCaptureImage(m_nDevHandle, info.ImageType, imgRes, captureOptions);
            if (nRc >= DLL.IBSU_STATUS_OK)
            {
                // Display message for image acuisition
                string strMessage;
                strMessage = String.Format("{0}", info.PreCaptureMessage);
                _SetStatusBarMessage(strMessage);
                if (!m_chkAutoCapture.Checked)
                    strMessage += String.Format("\r\nPress button 'Take Result Image' when image is good!");

                _SetImageMessage(strMessage);
                m_strImageMessage = strMessage;

                _SetLEDs(m_nDevHandle, info, __LED_COLOR_RED__, true);
            }
            else
            {
                string strMessage;
                strMessage = String.Format("Failed to execute IBSU_BeginCaptureImage()");
                _SetStatusBarMessage(strMessage);
            }

            OnMsg_UpdateDisplayResources();
        }

        private delegate void OnMsg_DeviceCommunicationBreakDelegate();
        private void OnMsg_DeviceCommunicationBreak()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_DeviceCommunicationBreakDelegate(OnMsg_DeviceCommunicationBreak));

                return;
            }

        }

        private delegate void OnMsg_InitWarningDelegate();
        private void OnMsg_InitWarning()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_InitWarningDelegate(OnMsg_InitWarning));

                return;
            }

        }

        private delegate void OnMsg_DrawClientWindowDelegate();
        private void OnMsg_DrawClientWindow()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_DrawClientWindowDelegate(OnMsg_DrawClientWindow));

                return;
            }

        }

        private delegate void OnMsg_UpdateDeviceListDelegate();
        private void OnMsg_UpdateDeviceList()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateDeviceListDelegate(OnMsg_UpdateDeviceList));

                return;
            }

            bool idle = !m_bInitializing && (m_nCurrentCaptureStep == -1);
            if (idle)
            {
                m_btnCaptureStop.Enabled = false;
                m_btnCaptureStart.Enabled = false;
            }

            // store currently selected device
            string strSelectedText = "";
            int selectedDev = m_cboUsbDevices.SelectedIndex;
            if (selectedDev > -1)
                strSelectedText = m_cboUsbDevices.Text;

            m_cboUsbDevices.Items.Clear();
            m_cboUsbDevices.Items.Add("- Please select -");

            // populate combo box
            int devices = 0;
            DLL._IBSU_GetDeviceCount(ref devices);

            selectedDev = 0;
            for (int i = 0; i < devices; i++)
            {
                DLL.IBSU_DeviceDesc devDesc = new DLL.IBSU_DeviceDesc();
                if (DLL._IBSU_GetDeviceDescription(i, ref devDesc) < DLL.IBSU_STATUS_OK)
                    continue;

                string strDevice;
                if (devDesc.productName[0] == 0)
                    strDevice = "unknown device";
                else
                    strDevice = devDesc.productName + "_v" + devDesc.fwVersion + "_" + devDesc.serialNumber + "(" + devDesc.interfaceType + ")";

                m_cboUsbDevices.Items.Add(strDevice);
                if (strDevice == strSelectedText)
                    selectedDev = i + 1;  
            }

            if ((selectedDev == 0) && (m_cboUsbDevices.Items.Count == 2))
                selectedDev = 1;

            m_cboUsbDevices.SelectedIndex = selectedDev;
            m_cboUsbDevices.Update();

            if (idle)
            {
                m_cboUsbDevices_SelectedIndexChanged(null, null);
                _UpdateCaptureSequences();
            }
        }

        private delegate void OnMsg_UpdateDisplayResourcesDelegate();
        private void OnMsg_UpdateDisplayResources()
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateDisplayResourcesDelegate(OnMsg_UpdateDisplayResources));

                return;
            }

            bool selectedDev = m_cboUsbDevices.SelectedIndex > 0;
            bool captureSeq = m_cboCaptureSeq.SelectedIndex > 0;
            bool idle = !m_bInitializing && (m_nCurrentCaptureStep == -1);
            bool active = !m_bInitializing && (m_nCurrentCaptureStep != -1);
            bool uninitializedDev = selectedDev && (m_nDevHandle == -1);


            m_cboUsbDevices.Enabled = idle;
            m_cboCaptureSeq.Enabled = selectedDev && idle;

            m_btnCaptureStart.Enabled = captureSeq;
            m_btnCaptureStop.Enabled = active;

            m_chkAutoContrast.Enabled = selectedDev && idle;
            m_chkAutoCapture.Enabled = selectedDev && idle;
            m_chkIgnoreFingerCount.Enabled = selectedDev && idle;
            m_chkSaveImages.Enabled = selectedDev && idle;
            m_btnImageFolder.Enabled = selectedDev && idle;

            m_chkUseClearPlaten.Enabled = uninitializedDev;

            string strCaption = "";
            if (active)
                strCaption = "Take Result Image";
            else if (!active && !m_bInitializing)
                strCaption = "Start";

            m_btnCaptureStart.Text = strCaption;
        }

        private delegate void OnMsg_UpdateStatusMessageDelegate(string message);
        private void OnMsg_UpdateStatusMessage(string message)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateStatusMessageDelegate(OnMsg_UpdateStatusMessage),
                    new object[] { message });

                return;
            }

            _SetStatusBarMessage(message);
        }

        private delegate void OnMsg_UpdateImageMessageDelegate(string message);
        private void OnMsg_UpdateImageMessage(string message)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateImageMessageDelegate(OnMsg_UpdateImageMessage),
                    new object[] { message });

                return;
            }

            _SetImageMessage(message);
        }

        private delegate void OnMsg_BeepDelegate(int beepType);
        private void OnMsg_Beep(int beepType)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_BeepDelegate(OnMsg_Beep),
                    new object[] { beepType });

                return;
            }

            if (beepType == __BEEP_FAIL__)
                _BeepFail();
            else if (beepType == __BEEP_SUCCESS__)
                _BeepSuccess();
            else if (beepType == __BEEP_OK__)
                _BeepOk();
            else if (beepType == __BEEP_DEVICE_COMMUNICATION_BREAK__)
                _BeepDeviceCommunicationBreak();
        }

        private delegate void OnMsg_UpdateNFIQScoreDelegate(string score);
        private void OnMsg_UpdateNFIQScore(string score)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateNFIQScoreDelegate(OnMsg_UpdateNFIQScore),
                    new object[] { score });

                return;
            }

            m_txtNFIQScore.Text = score;
        }

        private delegate void OnMsg_UpdateSpoofResultDelegate(string result);
        private void OnMsg_UpdateSpoofResult(string result)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_UpdateSpoofResultDelegate(OnMsg_UpdateSpoofResult),
                    new object[] { result });

                return;
            }
            m_txtSpoofResult.Text = result;
        }

        private delegate void OnMsg_AskRecaptureDelegate(int imageStatus);
        private void OnMsg_AskRecapture(int imageStatus)
        {
            // Check if we need to call beginInvoke.
            if (this.InvokeRequired)
            {
                // Pass the same function to BeginInvoke,
                // but the call would come on the correct
                // thread and InvokeRequired will be false
                this.BeginInvoke(new OnMsg_AskRecaptureDelegate(OnMsg_AskRecapture),
                    new object[] { imageStatus });

                return;
            }

            String strValue;

            strValue = String.Format("[Warning = {0}] Do you want a recapture?", imageStatus);

            if (MessageBox.Show(strValue, "IBScanUltimateSDK", MessageBoxButtons.YesNo) == DialogResult.Yes)
            {
                m_nCurrentCaptureStep = m_nCurrentCaptureStep - 1;
            }

            OnMsg_CaptureSeqNext();
        }



        ///////////////////////////////////////////////////////////////////////////////////////////
        // Form event
        ///////////////////////////////////////////////////////////////////////////////////////////
        private void SDKMainForm_Load(object sender, EventArgs e)
        {
            m_nDevHandle = -1;
            m_nCurrentCaptureStep = -1;
            m_bInitializing = false;
            m_strImageMessage = "";
            m_bNeedClearPlaten = false;
            m_bSaveWarningOfClearPlaten = false;
            m_bDevLocked = false;

            m_chkAutoContrast.Checked = true;
            m_chkAutoCapture.Checked = true;
            m_chkUseClearPlaten.Checked = true;
            m_chkNFIQScore.Checked = true;
            m_chkEnableSpoof.Checked = false ;
            m_chkDrawSegmentImage.Checked = true;
            m_chkDetectSmear.Checked = true;
            m_cboSmearLevel.Items.Clear();
            m_cboSmearLevel.Items.Add("LOW");
            m_cboSmearLevel.Items.Add("MEDIUM");
            m_cboSmearLevel.Items.Add("HIGH");
            m_cboSmearLevel.SelectedIndex = 1;
            m_cboSpoofLevel.Items.Clear();
            m_cboSpoofLevel.Items.Add("1");
            m_cboSpoofLevel.Items.Add("2");
            m_cboSpoofLevel.Items.Add("3");
            m_cboSpoofLevel.Items.Add("4");
            m_cboSpoofLevel.Items.Add("5");
            m_cboSpoofLevel.SelectedIndex = 2;


            m_sliderContrast.SetRange(DLL.IBSU_MIN_CONTRAST_VALUE, DLL.IBSU_MAX_CONTRAST_VALUE);
            m_sliderContrast.Value = 0;
            m_sliderContrast.TickFrequency = 5;
            m_txtContrast.Text = "0";

            m_verInfo = new DLL.IBSU_SdkVersion();
            DLL._IBSU_GetSDKVersion(ref m_verInfo);
            string titleName = "IntegrationSample for C#";
            this.Text = titleName;            

            m_callbackDeviceCommunicationBreak = new DLL.IBSU_Callback(OnEvent_DeviceCommunicationBreak);
            m_callbackPreviewImage = new DLL.IBSU_CallbackPreviewImage(OnEvent_PreviewImage);
            m_callbackFingerCount = new DLL.IBSU_CallbackFingerCount(OnEvent_FingerCount);
            m_callbackFingerQuality = new DLL.IBSU_CallbackFingerQuality(OnEvent_FingerQuality);
            m_callbackDeviceCount = new DLL.IBSU_CallbackDeviceCount(OnEvent_DeviceCount);
            m_callbackInitProgress = new DLL.IBSU_CallbackInitProgress(OnEvent_InitProgress);
            m_callbackTakingAcquisition = new DLL.IBSU_CallbackTakingAcquisition(OnEvent_TakingAcquisition);
            m_callbackCompleteAcquisition = new DLL.IBSU_CallbackCompleteAcquisition(OnEvent_CompleteAcquisition);
            m_callbackClearPlaten = new DLL.IBSU_CallbackClearPlatenAtCapture(OnEvent_ClearPlatenAtCapture);
            m_callbackResultImageEx = new DLL.IBSU_CallbackResultImageEx(OnEvent_ResultImageEx);
            m_callbackPressedKeyButtons = new DLL.IBSU_CallbackKeyButtons(OnEvent_PressedKeyButtons);

            DLL._IBSU_RegisterCallbacks(0, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_DEVICE_COUNT, m_callbackDeviceCount, this.Handle);
            DLL._IBSU_RegisterCallbacks(0, DLL.IBSU_Events.ENUM_IBSU_ESSENTIAL_EVENT_INIT_PROGRESS, m_callbackInitProgress, this.Handle);


            OnMsg_UpdateDeviceList();
        }

        private void m_btnCaptureStart_Click(object sender, EventArgs e)
        {
            OnMsg_CaptureStartClick();
        }

        private void m_btnCaptureStop_Click(object sender, EventArgs e)
        {
            OnMsg_CaptureStopClick();
        }

        private void m_btnImageFolder_Click(object sender, EventArgs e)
        {
            if (folderBrowserDialog1.ShowDialog() == DialogResult.OK)
            {
                m_ImgSaveFolder = folderBrowserDialog1.SelectedPath;
            }

            if (DLL._IBSU_IsWritableDirectory(m_ImgSaveFolder, true) != DLL.IBSU_STATUS_OK)
                System.Windows.Forms.MessageBox.Show("You don't have writing permission on this folder\r\nPlease select another folder (e.g. desktop folder)");
        }

        private void Timer_StatusFingerQuality_Tick(object sender, EventArgs e)
        {
            Boolean idle = !m_bInitializing && (m_nCurrentCaptureStep == -1);

            if (!idle)
            {
                if (m_bNeedClearPlaten && m_bBlank)
                {
                    if (m_bSaveWarningOfClearPlaten == false)
                    {
                        _ModifyOverlayForWarningOfClearPlaten(true);
                        m_bSaveWarningOfClearPlaten = true;
                    }
                }
                else
                {
                    if (m_bSaveWarningOfClearPlaten == true)
                    {
                        _ModifyOverlayForWarningOfClearPlaten(false);
                        m_bSaveWarningOfClearPlaten = false;
                    }
                }
            }

            m_picScanner.Invalidate(false);
            if( m_bNeedClearPlaten )
                m_bBlank = !m_bBlank;
        }

        private void SDKMainForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            _ReleaseDevice();
        }

        private void m_cboUsbDevices_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (m_cboUsbDevices.SelectedIndex == m_nSelectedDevIndex)
                return;

            Cursor = Cursors.WaitCursor;

            m_nSelectedDevIndex = m_cboUsbDevices.SelectedIndex;
            if (m_nDevHandle != -1)
            {
                m_btnCaptureStop_Click(sender, e);
                _ReleaseDevice();
            }

            _UpdateCaptureSequences();

            Cursor = Cursors.Default;
        }

        private void m_sliderContrast_Scroll(object sender, EventArgs e)
        {
	        int pos = m_sliderContrast.Value;
            m_txtContrast.Text = m_sliderContrast.Value.ToString();
	        DLL._IBSU_SetContrast(m_nDevHandle, pos);
        }

        private void m_chkAutoContrast_CheckedChanged(object sender, EventArgs e)
        {
            if (m_chkAutoContrast.Checked)
            {
                m_sliderContrast.Enabled = false;
                m_txtContrast.Enabled = false;
                m_staticContrast.Enabled = false;
            }
            else
            {
                m_sliderContrast.Enabled = true;
                m_txtContrast.Enabled = true;
                m_staticContrast.Enabled = true;
            }
        }

        private void m_cboCaptureSeq_SelectedIndexChanged(object sender, EventArgs e)
        {
            OnMsg_UpdateDisplayResources();
        }

        private void m_picIBLogo_Paint(object sender, PaintEventArgs e)
        {
            string message = String.Format("SDK v{0}", m_verInfo.Product);
            e.Graphics.DrawString(message, new Font("MS Sans Serif", 24), Brushes.White, 560, 15);
            e.Graphics.DrawString("Copyright (c) Integrated Biometrics", new Font("MS Sans Serif", 8), Brushes.White, 560, 52);
        }

        private void m_picScanner_Paint(object sender, PaintEventArgs e)
        {
            SolidBrush hbr_finger;
//            SolidBrush hbr_touch;

            for (int i = 0; i < 4; i++)
            {
                if (m_bNeedClearPlaten)
                {
                    if (m_bBlank)
                        hbr_finger = new SolidBrush(Color.Red);
                    else
                        hbr_finger = new SolidBrush(Color.FromArgb(114, 114, 114));
                }
                else
                {
                    switch (m_FingerQuality[i])
                    {
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_GOOD:
                            hbr_finger = new SolidBrush(Color.Green);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_FAIR:
                            hbr_finger = new SolidBrush(Color.Orange);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_POOR:
                            hbr_finger = new SolidBrush(Color.Red);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_FINGER_NOT_PRESENT:
                            hbr_finger = new SolidBrush(Color.FromArgb(114, 114, 114));
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_INVALID_AREA_TOP:
                            hbr_finger = new SolidBrush(Color.Red);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_INVALID_AREA_BOTTOM:
                            hbr_finger = new SolidBrush(Color.Red);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_INVALID_AREA_LEFT:
                            hbr_finger = new SolidBrush(Color.Red);
                            break;
                        case DLL.IBSU_FingerQualityState.ENUM_IBSU_QUALITY_INVALID_AREA_RIGHT:
                            hbr_finger = new SolidBrush(Color.Red);
                            break;
                        default:
                            return;
                    }
                }

                _DrawRoundRect(e.Graphics, hbr_finger, 17 + i * 22, 47, 19, 70, 9);
            }

            // Draw detected finger on the touch sensor
/*            int touchInValue = 0;
            DLL._IBSU_IsTouchedFinger(m_nDevHandle, ref touchInValue);
            if (touchInValue == 1)
                hbr_touch = new SolidBrush(Color.Green);
            else
                hbr_touch = new SolidBrush(Color.FromArgb(78, 78, 78));

            _DrawRoundRect(e.Graphics, hbr_touch, 15, 112, 85, 5, 2);
*/
        }
    }
}

