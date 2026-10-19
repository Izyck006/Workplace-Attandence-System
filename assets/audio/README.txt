This folder holds pre-rendered MP3 voice clips for the attendance kiosk.
If audio clips are placed here, the app will play them instantly with 0ms latency and 0 API cost.

Available filename mappings:
- welcome_system.mp3  -> Played when the attendance kiosk opens ("Welcome to Randaframes Attendance System.")
- welcome_user.mp3    -> Played when an employee clocks in ("Welcome!")
- goodbye.mp3         -> Played when an employee clocks out ("Goodbye, have a great day!")
- already_clocked.mp3 -> Played when an employee is already clocked in ("You are already clocked in.")
- scan_error.mp3      -> Played when a fingerprint scan is not recognized ("Fingerprint not recognized. Please scan again.")

If an employee's specific name is to be spoken (e.g. "Welcome, Amina"), the system uses your ElevenLabs API key and caches the audio dynamically!
