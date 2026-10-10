namespace IBScanUltimate_SampleForCSharp
{
    partial class SDKMainForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if( m_initThread != null )
                m_initThread.Abort();

            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(SDKMainForm));
            this.lbDeviceList = new System.Windows.Forms.Label();
            this.m_cboUsbDevices = new System.Windows.Forms.ComboBox();
            this.m_cboSpoofLevel = new System.Windows.Forms.ComboBox();
            this.m_chkEnableSpoof = new System.Windows.Forms.CheckBox();
            this.m_cboSmearLevel = new System.Windows.Forms.ComboBox();
            this.m_chkDetectSmear = new System.Windows.Forms.CheckBox();
            this.m_chkInvalidArea = new System.Windows.Forms.CheckBox();
            this.m_chkDrawSegmentImage = new System.Windows.Forms.CheckBox();
            this.m_txtNFIQScore = new System.Windows.Forms.Label();
            this.m_chkNFIQScore = new System.Windows.Forms.CheckBox();
            this.m_chkUseClearPlaten = new System.Windows.Forms.CheckBox();
            this.m_picScanner = new System.Windows.Forms.PictureBox();
            this.m_txtContrast = new System.Windows.Forms.Label();
            this.m_sliderContrast = new System.Windows.Forms.TrackBar();
            this.m_staticContrast = new System.Windows.Forms.Label();
            this.m_btnCaptureStart = new System.Windows.Forms.Button();
            this.m_btnCaptureStop = new System.Windows.Forms.Button();
            this.m_btnImageFolder = new System.Windows.Forms.Button();
            this.m_chkSaveImages = new System.Windows.Forms.CheckBox();
            this.m_chkIgnoreFingerCount = new System.Windows.Forms.CheckBox();
            this.m_chkAutoCapture = new System.Windows.Forms.CheckBox();
            this.m_chkAutoContrast = new System.Windows.Forms.CheckBox();
            this.m_cboCaptureSeq = new System.Windows.Forms.ComboBox();
            this.m_FrameImage = new System.Windows.Forms.Label();
            this.m_txtStatusMessage = new System.Windows.Forms.Label();
            this.Timer_StatusFingerQuality = new System.Windows.Forms.Timer(this.components);
            this.folderBrowserDialog1 = new System.Windows.Forms.FolderBrowserDialog();
            this.m_picIBLogo = new System.Windows.Forms.PictureBox();
            this.panel1 = new System.Windows.Forms.Panel();
            this.panel2 = new System.Windows.Forms.Panel();
            this.lbCapture = new System.Windows.Forms.Label();
            this.panel3 = new System.Windows.Forms.Panel();
            this.m_picLockStatus = new System.Windows.Forms.PictureBox();
            this.lbLockStatus = new System.Windows.Forms.Label();
            this.lbStatus = new System.Windows.Forms.Label();
            this.m_txtSpoofResult = new System.Windows.Forms.Label();
            ((System.ComponentModel.ISupportInitialize)(this.m_picScanner)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.m_sliderContrast)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.m_picIBLogo)).BeginInit();
            this.panel1.SuspendLayout();
            this.panel2.SuspendLayout();
            this.panel3.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.m_picLockStatus)).BeginInit();
            this.SuspendLayout();
            // 
            // lbDeviceList
            // 
            this.lbDeviceList.BackColor = System.Drawing.Color.Gray;
            this.lbDeviceList.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbDeviceList.ForeColor = System.Drawing.Color.White;
            this.lbDeviceList.Image = global::IBScanUltimate_SampleForCSharp.Properties.Resources.Devices;
            this.lbDeviceList.Location = new System.Drawing.Point(7, 6);
            this.lbDeviceList.Name = "lbDeviceList";
            this.lbDeviceList.Size = new System.Drawing.Size(279, 20);
            this.lbDeviceList.TabIndex = 1;
            this.lbDeviceList.Text = "                 ";
            // 
            // m_cboUsbDevices
            // 
            this.m_cboUsbDevices.FormattingEnabled = true;
            this.m_cboUsbDevices.Location = new System.Drawing.Point(7, 31);
            this.m_cboUsbDevices.Name = "m_cboUsbDevices";
            this.m_cboUsbDevices.Size = new System.Drawing.Size(279, 21);
            this.m_cboUsbDevices.TabIndex = 0;
            this.m_cboUsbDevices.SelectedIndexChanged += new System.EventHandler(this.m_cboUsbDevices_SelectedIndexChanged);
            // 
            // m_cboSpoofLevel
            // 
            this.m_cboSpoofLevel.FormattingEnabled = true;
            this.m_cboSpoofLevel.Location = new System.Drawing.Point(236, 149);
            this.m_cboSpoofLevel.Name = "m_cboSpoofLevel";
            this.m_cboSpoofLevel.Size = new System.Drawing.Size(50, 21);
            this.m_cboSpoofLevel.TabIndex = 19;
            // 
            // m_chkEnableSpoof
            // 
            this.m_chkEnableSpoof.Location = new System.Drawing.Point(132, 152);
            this.m_chkEnableSpoof.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkEnableSpoof.Name = "m_chkEnableSpoof";
            this.m_chkEnableSpoof.Size = new System.Drawing.Size(98, 18);
            this.m_chkEnableSpoof.TabIndex = 18;
            this.m_chkEnableSpoof.Text = "Enable Spoof";
            this.m_chkEnableSpoof.UseVisualStyleBackColor = true;
            // 
            // m_cboSmearLevel
            // 
            this.m_cboSmearLevel.FormattingEnabled = true;
            this.m_cboSmearLevel.Location = new System.Drawing.Point(236, 126);
            this.m_cboSmearLevel.Name = "m_cboSmearLevel";
            this.m_cboSmearLevel.Size = new System.Drawing.Size(50, 21);
            this.m_cboSmearLevel.TabIndex = 17;
            // 
            // m_chkDetectSmear
            // 
            this.m_chkDetectSmear.Location = new System.Drawing.Point(132, 128);
            this.m_chkDetectSmear.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkDetectSmear.Name = "m_chkDetectSmear";
            this.m_chkDetectSmear.Size = new System.Drawing.Size(89, 18);
            this.m_chkDetectSmear.TabIndex = 16;
            this.m_chkDetectSmear.Text = "Detect smear";
            this.m_chkDetectSmear.UseVisualStyleBackColor = true;
            // 
            // m_chkInvalidArea
            // 
            this.m_chkInvalidArea.Location = new System.Drawing.Point(132, 104);
            this.m_chkInvalidArea.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkInvalidArea.Name = "m_chkInvalidArea";
            this.m_chkInvalidArea.Size = new System.Drawing.Size(122, 18);
            this.m_chkInvalidArea.TabIndex = 15;
            this.m_chkInvalidArea.Text = "Invalid area";
            this.m_chkInvalidArea.UseVisualStyleBackColor = true;
            // 
            // m_chkDrawSegmentImage
            // 
            this.m_chkDrawSegmentImage.Location = new System.Drawing.Point(132, 50);
            this.m_chkDrawSegmentImage.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkDrawSegmentImage.Name = "m_chkDrawSegmentImage";
            this.m_chkDrawSegmentImage.Size = new System.Drawing.Size(154, 30);
            this.m_chkDrawSegmentImage.TabIndex = 14;
            this.m_chkDrawSegmentImage.Text = "Draw quadrangle for segment image";
            this.m_chkDrawSegmentImage.UseVisualStyleBackColor = true;
            // 
            // m_txtNFIQScore
            // 
            this.m_txtNFIQScore.BackColor = System.Drawing.Color.White;
            this.m_txtNFIQScore.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.m_txtNFIQScore.Location = new System.Drawing.Point(224, 83);
            this.m_txtNFIQScore.Name = "m_txtNFIQScore";
            this.m_txtNFIQScore.Size = new System.Drawing.Size(63, 18);
            this.m_txtNFIQScore.TabIndex = 12;
            this.m_txtNFIQScore.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // m_chkNFIQScore
            // 
            this.m_chkNFIQScore.Location = new System.Drawing.Point(132, 83);
            this.m_chkNFIQScore.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkNFIQScore.Name = "m_chkNFIQScore";
            this.m_chkNFIQScore.Size = new System.Drawing.Size(56, 18);
            this.m_chkNFIQScore.TabIndex = 5;
            this.m_chkNFIQScore.Text = "NFIQ";
            this.m_chkNFIQScore.UseVisualStyleBackColor = true;
            // 
            // m_chkUseClearPlaten
            // 
            this.m_chkUseClearPlaten.Location = new System.Drawing.Point(132, 29);
            this.m_chkUseClearPlaten.Margin = new System.Windows.Forms.Padding(3, 3, 0, 3);
            this.m_chkUseClearPlaten.Name = "m_chkUseClearPlaten";
            this.m_chkUseClearPlaten.Size = new System.Drawing.Size(131, 18);
            this.m_chkUseClearPlaten.TabIndex = 4;
            this.m_chkUseClearPlaten.Text = "Detect clear platen";
            this.m_chkUseClearPlaten.UseVisualStyleBackColor = true;
            // 
            // m_picScanner
            // 
            this.m_picScanner.ErrorImage = null;
            this.m_picScanner.Image = ((System.Drawing.Image)(resources.GetObject("m_picScanner.Image")));
            this.m_picScanner.Location = new System.Drawing.Point(6, 29);
            this.m_picScanner.Name = "m_picScanner";
            this.m_picScanner.Size = new System.Drawing.Size(120, 146);
            this.m_picScanner.TabIndex = 5;
            this.m_picScanner.TabStop = false;
            this.m_picScanner.Paint += new System.Windows.Forms.PaintEventHandler(this.m_picScanner_Paint);
            // 
            // m_txtContrast
            // 
            this.m_txtContrast.BackColor = System.Drawing.Color.White;
            this.m_txtContrast.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.m_txtContrast.Location = new System.Drawing.Point(248, 185);
            this.m_txtContrast.Name = "m_txtContrast";
            this.m_txtContrast.Size = new System.Drawing.Size(37, 18);
            this.m_txtContrast.TabIndex = 11;
            this.m_txtContrast.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // m_sliderContrast
            // 
            this.m_sliderContrast.AutoSize = false;
            this.m_sliderContrast.Location = new System.Drawing.Point(48, 184);
            this.m_sliderContrast.Maximum = 34;
            this.m_sliderContrast.Name = "m_sliderContrast";
            this.m_sliderContrast.Size = new System.Drawing.Size(194, 19);
            this.m_sliderContrast.TabIndex = 10;
            this.m_sliderContrast.TickFrequency = 5;
            this.m_sliderContrast.Scroll += new System.EventHandler(this.m_sliderContrast_Scroll);
            // 
            // m_staticContrast
            // 
            this.m_staticContrast.AutoSize = true;
            this.m_staticContrast.Location = new System.Drawing.Point(3, 184);
            this.m_staticContrast.Name = "m_staticContrast";
            this.m_staticContrast.Size = new System.Drawing.Size(46, 13);
            this.m_staticContrast.TabIndex = 9;
            this.m_staticContrast.Text = "Contrast";
            // 
            // m_btnCaptureStart
            // 
            this.m_btnCaptureStart.Location = new System.Drawing.Point(160, 152);
            this.m_btnCaptureStart.Name = "m_btnCaptureStart";
            this.m_btnCaptureStart.Size = new System.Drawing.Size(126, 27);
            this.m_btnCaptureStart.TabIndex = 8;
            this.m_btnCaptureStart.Text = "Start";
            this.m_btnCaptureStart.UseVisualStyleBackColor = true;
            this.m_btnCaptureStart.Click += new System.EventHandler(this.m_btnCaptureStart_Click);
            // 
            // m_btnCaptureStop
            // 
            this.m_btnCaptureStop.Location = new System.Drawing.Point(8, 152);
            this.m_btnCaptureStop.Name = "m_btnCaptureStop";
            this.m_btnCaptureStop.Size = new System.Drawing.Size(126, 27);
            this.m_btnCaptureStop.TabIndex = 7;
            this.m_btnCaptureStop.Text = "Stop";
            this.m_btnCaptureStop.UseVisualStyleBackColor = true;
            this.m_btnCaptureStop.Click += new System.EventHandler(this.m_btnCaptureStop_Click);
            // 
            // m_btnImageFolder
            // 
            this.m_btnImageFolder.Location = new System.Drawing.Point(100, 126);
            this.m_btnImageFolder.Name = "m_btnImageFolder";
            this.m_btnImageFolder.Size = new System.Drawing.Size(33, 19);
            this.m_btnImageFolder.TabIndex = 6;
            this.m_btnImageFolder.Text = "...";
            this.m_btnImageFolder.UseVisualStyleBackColor = true;
            this.m_btnImageFolder.Click += new System.EventHandler(this.m_btnImageFolder_Click);
            // 
            // m_chkSaveImages
            // 
            this.m_chkSaveImages.AutoSize = true;
            this.m_chkSaveImages.Location = new System.Drawing.Point(7, 128);
            this.m_chkSaveImages.Name = "m_chkSaveImages";
            this.m_chkSaveImages.Size = new System.Drawing.Size(87, 17);
            this.m_chkSaveImages.TabIndex = 5;
            this.m_chkSaveImages.Text = "Save images";
            this.m_chkSaveImages.UseVisualStyleBackColor = true;
            // 
            // m_chkIgnoreFingerCount
            // 
            this.m_chkIgnoreFingerCount.AutoSize = true;
            this.m_chkIgnoreFingerCount.Location = new System.Drawing.Point(7, 105);
            this.m_chkIgnoreFingerCount.Name = "m_chkIgnoreFingerCount";
            this.m_chkIgnoreFingerCount.Size = new System.Drawing.Size(258, 17);
            this.m_chkIgnoreFingerCount.TabIndex = 4;
            this.m_chkIgnoreFingerCount.Text = "Trigger invalid finger count on auto-capture mode";
            this.m_chkIgnoreFingerCount.UseVisualStyleBackColor = true;
            // 
            // m_chkAutoCapture
            // 
            this.m_chkAutoCapture.AutoSize = true;
            this.m_chkAutoCapture.Location = new System.Drawing.Point(8, 82);
            this.m_chkAutoCapture.Name = "m_chkAutoCapture";
            this.m_chkAutoCapture.Size = new System.Drawing.Size(181, 17);
            this.m_chkAutoCapture.TabIndex = 3;
            this.m_chkAutoCapture.Text = "Automatic capture for fingerprints";
            this.m_chkAutoCapture.UseVisualStyleBackColor = true;
            // 
            // m_chkAutoContrast
            // 
            this.m_chkAutoContrast.AutoSize = true;
            this.m_chkAutoContrast.Location = new System.Drawing.Point(8, 59);
            this.m_chkAutoContrast.Name = "m_chkAutoContrast";
            this.m_chkAutoContrast.Size = new System.Drawing.Size(172, 17);
            this.m_chkAutoContrast.TabIndex = 2;
            this.m_chkAutoContrast.Text = "Automatic contrast optimization";
            this.m_chkAutoContrast.UseVisualStyleBackColor = true;
            this.m_chkAutoContrast.CheckedChanged += new System.EventHandler(this.m_chkAutoContrast_CheckedChanged);
            // 
            // m_cboCaptureSeq
            // 
            this.m_cboCaptureSeq.FormattingEnabled = true;
            this.m_cboCaptureSeq.Location = new System.Drawing.Point(7, 32);
            this.m_cboCaptureSeq.Name = "m_cboCaptureSeq";
            this.m_cboCaptureSeq.Size = new System.Drawing.Size(278, 21);
            this.m_cboCaptureSeq.TabIndex = 1;
            this.m_cboCaptureSeq.SelectedIndexChanged += new System.EventHandler(this.m_cboCaptureSeq_SelectedIndexChanged);
            // 
            // m_FrameImage
            // 
            this.m_FrameImage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.m_FrameImage.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.m_FrameImage.Location = new System.Drawing.Point(322, 90);
            this.m_FrameImage.Name = "m_FrameImage";
            this.m_FrameImage.Size = new System.Drawing.Size(480, 450);
            this.m_FrameImage.TabIndex = 2;
            // 
            // m_txtStatusMessage
            // 
            this.m_txtStatusMessage.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.m_txtStatusMessage.Location = new System.Drawing.Point(322, 566);
            this.m_txtStatusMessage.Name = "m_txtStatusMessage";
            this.m_txtStatusMessage.Size = new System.Drawing.Size(480, 23);
            this.m_txtStatusMessage.TabIndex = 3;
            this.m_txtStatusMessage.Text = "Ready";
            this.m_txtStatusMessage.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            // 
            // Timer_StatusFingerQuality
            // 
            this.Timer_StatusFingerQuality.Enabled = true;
            this.Timer_StatusFingerQuality.Interval = 500;
            this.Timer_StatusFingerQuality.Tick += new System.EventHandler(this.Timer_StatusFingerQuality_Tick);
            // 
            // m_picIBLogo
            // 
            this.m_picIBLogo.ErrorImage = null;
            this.m_picIBLogo.Image = global::IBScanUltimate_SampleForCSharp.Properties.Resources.IB_logo;
            this.m_picIBLogo.Location = new System.Drawing.Point(-1, 0);
            this.m_picIBLogo.Name = "m_picIBLogo";
            this.m_picIBLogo.Size = new System.Drawing.Size(818, 75);
            this.m_picIBLogo.TabIndex = 6;
            this.m_picIBLogo.TabStop = false;
            this.m_picIBLogo.Paint += new System.Windows.Forms.PaintEventHandler(this.m_picIBLogo_Paint);
            // 
            // panel1
            // 
            this.panel1.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(230)))), ((int)(((byte)(230)))), ((int)(((byte)(230)))));
            this.panel1.Controls.Add(this.lbDeviceList);
            this.panel1.Controls.Add(this.m_cboUsbDevices);
            this.panel1.Location = new System.Drawing.Point(12, 90);
            this.panel1.Name = "panel1";
            this.panel1.Size = new System.Drawing.Size(293, 61);
            this.panel1.TabIndex = 20;
            // 
            // panel2
            // 
            this.panel2.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(230)))), ((int)(((byte)(230)))), ((int)(((byte)(230)))));
            this.panel2.Controls.Add(this.m_txtContrast);
            this.panel2.Controls.Add(this.lbCapture);
            this.panel2.Controls.Add(this.m_sliderContrast);
            this.panel2.Controls.Add(this.m_cboCaptureSeq);
            this.panel2.Controls.Add(this.m_staticContrast);
            this.panel2.Controls.Add(this.m_chkAutoContrast);
            this.panel2.Controls.Add(this.m_btnCaptureStart);
            this.panel2.Controls.Add(this.m_chkAutoCapture);
            this.panel2.Controls.Add(this.m_btnCaptureStop);
            this.panel2.Controls.Add(this.m_chkIgnoreFingerCount);
            this.panel2.Controls.Add(this.m_btnImageFolder);
            this.panel2.Controls.Add(this.m_chkSaveImages);
            this.panel2.Location = new System.Drawing.Point(13, 157);
            this.panel2.Name = "panel2";
            this.panel2.Size = new System.Drawing.Size(292, 212);
            this.panel2.TabIndex = 21;
            // 
            // lbCapture
            // 
            this.lbCapture.BackColor = System.Drawing.Color.Gray;
            this.lbCapture.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbCapture.ForeColor = System.Drawing.Color.White;
            this.lbCapture.Image = global::IBScanUltimate_SampleForCSharp.Properties.Resources.Fingerprint_Status;
            this.lbCapture.Location = new System.Drawing.Point(7, 6);
            this.lbCapture.Name = "lbCapture";
            this.lbCapture.Size = new System.Drawing.Size(279, 21);
            this.lbCapture.TabIndex = 1;
            this.lbCapture.Text = "    ";
            // 
            // panel3
            // 
            this.panel3.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(230)))), ((int)(((byte)(230)))), ((int)(((byte)(230)))));
            this.panel3.Controls.Add(this.m_txtSpoofResult);
            this.panel3.Controls.Add(this.m_picLockStatus);
            this.panel3.Controls.Add(this.lbLockStatus);
            this.panel3.Controls.Add(this.lbStatus);
            this.panel3.Controls.Add(this.m_picScanner);
            this.panel3.Controls.Add(this.m_chkUseClearPlaten);
            this.panel3.Controls.Add(this.m_cboSpoofLevel);
            this.panel3.Controls.Add(this.m_chkNFIQScore);
            this.panel3.Controls.Add(this.m_chkEnableSpoof);
            this.panel3.Controls.Add(this.m_txtNFIQScore);
            this.panel3.Controls.Add(this.m_cboSmearLevel);
            this.panel3.Controls.Add(this.m_chkDrawSegmentImage);
            this.panel3.Controls.Add(this.m_chkDetectSmear);
            this.panel3.Controls.Add(this.m_chkInvalidArea);
            this.panel3.Location = new System.Drawing.Point(12, 375);
            this.panel3.Name = "panel3";
            this.panel3.Size = new System.Drawing.Size(293, 214);
            this.panel3.TabIndex = 22;
            // 
            // m_picLockStatus
            // 
            this.m_picLockStatus.ErrorImage = null;
            this.m_picLockStatus.Image = ((System.Drawing.Image)(resources.GetObject("m_picLockStatus.Image")));
            this.m_picLockStatus.Location = new System.Drawing.Point(6, 177);
            this.m_picLockStatus.Name = "m_picLockStatus";
            this.m_picLockStatus.Size = new System.Drawing.Size(27, 28);
            this.m_picLockStatus.TabIndex = 23;
            this.m_picLockStatus.TabStop = false;
            this.m_picLockStatus.Visible = false;
            // 
            // lbLockStatus
            // 
            this.lbLockStatus.AutoSize = true;
            this.lbLockStatus.BackColor = System.Drawing.SystemColors.Control;
            this.lbLockStatus.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbLockStatus.ForeColor = System.Drawing.Color.ForestGreen;
            this.lbLockStatus.Location = new System.Drawing.Point(43, 183);
            this.lbLockStatus.Name = "lbLockStatus";
            this.lbLockStatus.Size = new System.Drawing.Size(67, 16);
            this.lbLockStatus.TabIndex = 1;
            this.lbLockStatus.Text = "LOCKED";
            this.lbLockStatus.Visible = false;
            // 
            // lbStatus
            // 
            this.lbStatus.BackColor = System.Drawing.Color.Gray;
            this.lbStatus.Font = new System.Drawing.Font("Microsoft Sans Serif", 9.75F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lbStatus.ForeColor = System.Drawing.Color.White;
            this.lbStatus.Image = global::IBScanUltimate_SampleForCSharp.Properties.Resources.Device_Status;
            this.lbStatus.Location = new System.Drawing.Point(7, 6);
            this.lbStatus.Name = "lbStatus";
            this.lbStatus.Size = new System.Drawing.Size(280, 18);
            this.lbStatus.TabIndex = 1;
            this.lbStatus.Text = "                    ";
            // 
            // m_txtSpoofResult
            // 
            this.m_txtSpoofResult.BackColor = System.Drawing.Color.White;
            this.m_txtSpoofResult.BorderStyle = System.Windows.Forms.BorderStyle.Fixed3D;
            this.m_txtSpoofResult.Location = new System.Drawing.Point(132, 173);
            this.m_txtSpoofResult.Name = "m_txtSpoofResult";
            this.m_txtSpoofResult.Size = new System.Drawing.Size(154, 18);
            this.m_txtSpoofResult.TabIndex = 24;
            this.m_txtSpoofResult.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            // 
            // SDKMainForm
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.White;
            this.ClientSize = new System.Drawing.Size(814, 601);
            this.Controls.Add(this.panel3);
            this.Controls.Add(this.panel2);
            this.Controls.Add(this.panel1);
            this.Controls.Add(this.m_txtStatusMessage);
            this.Controls.Add(this.m_picIBLogo);
            this.Controls.Add(this.m_FrameImage);
            this.DoubleBuffered = true;
            this.Font = new System.Drawing.Font("Microsoft Sans Serif", 8.25F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.Location = new System.Drawing.Point(11, 120);
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "SDKMainForm";
            this.Text = "IntegrationSample for C#";
            this.Load += new System.EventHandler(this.SDKMainForm_Load);
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.SDKMainForm_FormClosing);
            ((System.ComponentModel.ISupportInitialize)(this.m_picScanner)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.m_sliderContrast)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.m_picIBLogo)).EndInit();
            this.panel1.ResumeLayout(false);
            this.panel2.ResumeLayout(false);
            this.panel2.PerformLayout();
            this.panel3.ResumeLayout(false);
            this.panel3.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.m_picLockStatus)).EndInit();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.CheckBox m_chkAutoContrast;
        private System.Windows.Forms.ComboBox m_cboCaptureSeq;
        private System.Windows.Forms.CheckBox m_chkIgnoreFingerCount;
        private System.Windows.Forms.CheckBox m_chkAutoCapture;
        private System.Windows.Forms.Label m_FrameImage;
        private System.Windows.Forms.Button m_btnImageFolder;
        private System.Windows.Forms.CheckBox m_chkSaveImages;
        private System.Windows.Forms.Label m_staticContrast;
        private System.Windows.Forms.Button m_btnCaptureStart;
        private System.Windows.Forms.Button m_btnCaptureStop;
        private System.Windows.Forms.TrackBar m_sliderContrast;
        private System.Windows.Forms.Label m_txtContrast;
        private System.Windows.Forms.Label m_txtStatusMessage;
        private System.Windows.Forms.CheckBox m_chkUseClearPlaten;
        private System.Windows.Forms.Timer Timer_StatusFingerQuality;
        private System.Windows.Forms.FolderBrowserDialog folderBrowserDialog1;
        private System.Windows.Forms.PictureBox m_picScanner;
        private System.Windows.Forms.PictureBox m_picIBLogo;
        private System.Windows.Forms.Label m_txtNFIQScore;
        private System.Windows.Forms.CheckBox m_chkNFIQScore;
        private System.Windows.Forms.CheckBox m_chkDrawSegmentImage;
        private System.Windows.Forms.CheckBox m_chkInvalidArea;
        private System.Windows.Forms.CheckBox m_chkDetectSmear;
        private System.Windows.Forms.ComboBox m_cboSmearLevel;
        private System.Windows.Forms.ComboBox m_cboSpoofLevel;
        private System.Windows.Forms.CheckBox m_chkEnableSpoof;
        //private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.ComboBox m_cboUsbDevices;
        private System.Windows.Forms.Label lbDeviceList;
        private System.Windows.Forms.Panel panel1;
        private System.Windows.Forms.Panel panel2;
        private System.Windows.Forms.Label lbCapture;
        private System.Windows.Forms.Panel panel3;
        private System.Windows.Forms.Label lbStatus;
        private System.Windows.Forms.PictureBox m_picLockStatus;
        private System.Windows.Forms.Label lbLockStatus;
        private System.Windows.Forms.Label m_txtSpoofResult;
    }
}

