using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using HidSharp;
//using HidSharp.Reports;
//using HidSharp.Reports.Encodings;

namespace FitMi_Research_Puck
{
    public class HIDPuckDongle
    {
        #region Public static members

        public static Dictionary<string, Dictionary<string, HidPuckCommands>> Commands = new Dictionary<string, Dictionary<string, HidPuckCommands>>()
        {
            {   "red",
                new Dictionary<string, HidPuckCommands>()
                {
                    { "blink", HidPuckCommands.RBLINK },
                    { "pulse", HidPuckCommands.RPULSE }
                }
            },
            {
                "green",
                new Dictionary<string, HidPuckCommands>()
                {
                    { "blink", HidPuckCommands.GBLINK },
                    { "pulse", HidPuckCommands.GPULSE }
                }
            },
            {
                "blue",
                new Dictionary<string, HidPuckCommands>()
                {
                    { "blink", HidPuckCommands.BBLINK },
                    { "pulse", HidPuckCommands.BPULSE }
                }
            },
            {
                "motor",
                new Dictionary<string, HidPuckCommands>()
                {
                    { "blink", HidPuckCommands.MBLINK },
                    { "pulse", HidPuckCommands.MPULSE }
                }
            }
        };

        #endregion

        #region Data Members

        public int VendorID = 0x04d8;
        public int ProductID = 0x2742;
        public int Release = 0;
        public int Verbosity = 0;
        public bool IsOpen = false;
        public bool ReceivingData = false;

        public PuckPacket PuckPack0 = new PuckPacket();
        public PuckPacket PuckPack1 = new PuckPacket();

        public int RX_HardwareState = 0;
        public int RX_Channel = 0;
        public int Block0_Pipe = 0;
        public int Block1_Pipe = 1;
        public int EmptyDataCount = 0;
        public bool PlugState = false;

        public int QueueCapacity = 10;
        public Queue<List<int>> USB_OutQueue = new Queue<List<int>>();
        public Queue<Tuple<int, bool>> TouchQueue = new Queue<Tuple<int, bool>>();

        public List<DateTime> LastSent = new List<DateTime>() { DateTime.MinValue, DateTime.MinValue };
        public BackgroundWorker BackgroundThread = null;

        public HidStream DeviceStream;

        public object ThreadingLock = new object();

        public List<byte> Inpt = new List<byte>();

        #endregion

        #region Constructor

        public HIDPuckDongle()
        {
            BackgroundThread = new BackgroundWorker();
            BackgroundThread.WorkerReportsProgress = true;
            BackgroundThread.WorkerSupportsCancellation = true;
            BackgroundThread.DoWork += InputChecker;
        }
        
        #endregion

        public void Open ()
        {
            if (!IsPlugged())
            {
                return;
            }

            try
            {
                DeviceStream.Close();
            }
            catch (Exception)
            {
                //empty
            }

            var device_list = DeviceList.Local;
            HidDevice device = device_list.GetHidDeviceOrNull(this.VendorID, this.ProductID);
            bool success = device.TryOpen(out this.DeviceStream);
            
            //HidDeviceLoader device_loader = new HidDeviceLoader();
            //HidDevice device = device_loader.GetDeviceOrDefault(this.VendorID, this.ProductID);
            //bool success = device.TryOpen(out this.DeviceStream);
            
            IsOpen = true;
            BackgroundThread.RunWorkerAsync();

            PlugState = true;
            EmptyDataCount = 0;
            ReceivingData = false;
            CheckConnection();
            WaitForData();

            SendCommand(0, HidPuckCommands.GAMEON, 0x00, 0x01);
            SendCommand(1, HidPuckCommands.GAMEON, 0x00, 0x01);
        }

        public void CheckConnection ()
        {
            bool radio_working = false;
            for (int i = 0; i < 200; i++)
            {
                CheckForNewPuckData();
                if (PuckPack0.Connected || PuckPack1.Connected)
                {
                    radio_working = true;
                    break;
                }

                Thread.Sleep(1);
            }

            SendCommand(0, HidPuckCommands.DNGLRST, 0x00, 0x00);
            Thread.Sleep(600);
        }

        public void WaitForData ()
        {
            for (int i = 0; i < 200; i++)
            {
                Thread.Sleep(1);
                if (ReceivingData)
                    break;
            }
        }
        
        private void InputChecker(object sender, DoWorkEventArgs e)
        {
            int read_fail_count = 0;
            int too_many_fails = 70;
            int tick = 0;

            Dictionary<string, bool> touch_history = new Dictionary<string, bool>()
            {
                { "puck0", false },
                { "puck1", false }
            };

            while (IsOpen)
            {
                if (DeviceStream != null)
                {
                    byte[] inpt = DeviceStream.Read().ToList().GetRange(1, 62).ToArray();
                    lock (ThreadingLock)
                    {
                        Inpt = inpt.ToList();
                    }

                    if (Inpt == null || Inpt.Count == 0)
                    {
                        read_fail_count++;
                        if (read_fail_count > too_many_fails)
                        {
                            ReceivingData = false;
                        }
                    }
                    else
                    {
                        read_fail_count = 0;
                        ReceivingData = true;
                        CheckForTouch(Inpt.ToArray(), touch_history, 0);
                        CheckForTouch(Inpt.ToArray(), touch_history, 1);
                    }

                    if (USB_OutQueue.Count > 0)
                    {
                        //This may be incorrect....
                        DeviceStream.Write(USB_OutQueue.Dequeue().Select(x => (byte)x).ToArray());
                    }
                }
                
                Thread.Sleep(new TimeSpan(100));
            }

            for (int i = 0; i < 10; i++)
            {
                if (USB_OutQueue.Count > 0)
                {
                    if (DeviceStream != null)
                    {
                        DeviceStream.Write(USB_OutQueue.Dequeue().Select(x => (byte)x).ToArray());
                    }
                }
            }

            if (DeviceStream != null)
            {
                DeviceStream.Close();
            }
        }

        public void CheckForTouch (byte[] inpt, Dictionary<string, bool> touch_history, int puck_num)
        {
            int index = 29;
            if (puck_num == 1)
            {
                index = 59;
            }

            var status = inpt[index];
            var touch = (status & 0b0000_0100) >> 2;

            if (puck_num == 0)
            {
                if (touch > 0 && !touch_history["puck0"])
                {
                    if (TouchQueue.Count < QueueCapacity)
                    {
                        TouchQueue.Enqueue(new Tuple<int, bool>(0, true));
                    }
                }
                else if (touch == 0 && touch_history["puck0"])
                {
                    if (TouchQueue.Count < QueueCapacity)
                    {
                        TouchQueue.Enqueue(new Tuple<int, bool>(0, false));
                    }
                }

                touch_history["puck0"] = touch > 0 ? true : false;
            }
        }

        public void CheckForNewPuckData ()
        {
            if (ReceivingData)
            {
                try
                {
                    List<byte> this_thread_input = new List<byte>();
                    lock (ThreadingLock)
                    {
                        this_thread_input = Inpt.ToList();
                    }

                    Parse_RX_Data(this_thread_input.GetRange(60, 2).ToArray());
                    PuckPack0.Parse(this_thread_input.GetRange(0, 30).ToArray());
                    PuckPack1.Parse(this_thread_input.GetRange(30, 30).ToArray());

                    while (TouchQueue.Count > 0)
                    {
                        var t = TouchQueue.Dequeue();
                        var puck_num = t.Item1;
                        var state = t.Item2;

                        if (puck_num == 0 && state)
                        {
                            PuckPack0.Touch = state;
                        }
                        else if (puck_num == 1 && state)
                        {
                            PuckPack1.Touch = state;
                        }
                    }
                }
                catch (Exception)
                {
                    //empty
                }
            }
        }

        public void Parse_RX_Data (byte[] byte_array_rx_data)
        {
            var result = BitConverter.ToInt16(byte_array_rx_data, 0);
            RX_HardwareState = result >> 13;
            RX_Channel = (result & 0b0001_1111_1100_0000) >> 6;
            Block0_Pipe = (result & 0b111000) >> 3;
            Block1_Pipe = (result & 0b111);
        }

        public void Parse_RX_Data (string rxdata)
        {
            byte[] string_bytes = Encoding.ASCII.GetBytes(rxdata);
            Parse_RX_Data(string_bytes);
        }

        public void SendCommand (int puck_number, HidPuckCommands cmd, int msb, int lsb)
        {
            var command = (0b1110_0000 & (puck_number << 5)) | (byte)cmd;
            if (IsPlugged())
            {
                if (this.USB_OutQueue.Count < QueueCapacity)
                {
                    this.USB_OutQueue.Enqueue(new List<int>() { 0x00, command, msb, lsb });
                }
            }
        }

        public void NoteSending (string value)
        {
            //empty
        }

        public void Actuate (int puck_number, int duration, int amp, string atype = "blink", string actuator = "motor")
        {
            var puck_0_time_since_last_sent = (DateTime.Now - LastSent[0]).TotalSeconds;
            var puck_1_time_since_last_sent = (DateTime.Now - LastSent[1]).TotalSeconds;

            if (puck_number == 0 && puck_0_time_since_last_sent < 0.2)
                return;
            if (puck_number == 1 && puck_1_time_since_last_sent < 0.2)
                return;

            LastSent[puck_number] = DateTime.Now;
            var durbyte = Convert.ToInt32(Math.Min((duration * 255.0) / 1500.0, 255.0));
            amp = Math.Min(amp, 100);

            try
            {
                var cmd = HIDPuckDongle.Commands[actuator][atype];
                SendCommand(puck_number, cmd, durbyte, amp);
            }
            catch (Exception e)
            {
                //empty
            }
        }

        public void SetTouchBuzz (int puck_number, int value)
        {
            SendCommand(puck_number, HidPuckCommands.TOUCHBUZ, 0, value);
        }

        public void ChangeRXFrequency (int new_frequency)
        {
            SendCommand(0, HidPuckCommands.RXCHANGEFREQ, 0, new_frequency);
        }

        public void SetUSBPipes (int pack0_pipe = 0, int pack1_pipe = 1)
        {
            pack0_pipe = Math.Min(pack0_pipe, 5);
            pack1_pipe = Math.Min(pack1_pipe, 5);
            SendCommand(0, HidPuckCommands.SETUSBPIPES, pack0_pipe, pack1_pipe);
        }

        public void StartSpy (int spy_channel = 12, int duration = 100)
        {
            if (duration > 255)
            {
                duration = 255;
            }

            SendCommand(0, HidPuckCommands.CHANSPY, spy_channel, duration);
        }

        public void Stop ()
        {
            IsOpen = false;
        }

        public void Close ()
        {
            if (IsPlugged() && IsOpened())
            {
                SetTouchBuzz(0, 1);
                SetTouchBuzz(1, 1);
            }

            IsOpen = false;
            if (BackgroundThread != null && BackgroundThread.IsBusy)
            {
                BackgroundThread.CancelAsync();
            }
        }

        public bool IsPlugged ()
        {
            var device_list = DeviceList.Local;
            HidDevice device = device_list.GetHidDeviceOrNull(this.VendorID, this.ProductID);
            //HidDeviceLoader device_loader = new HidDeviceLoader();
            //HidDevice device = device_loader.GetDeviceOrDefault(this.VendorID, this.ProductID);
            return (device != null);
        }

        public bool IsOpened ()
        {
            return this.IsOpen;
        }

        public bool IsPluggedFast ()
        {
            return this.ReceivingData;
        }

        public HidDevice GetDeviceInfo ()
        {
            var device_list = DeviceList.Local;
            HidDevice device = device_list.GetHidDeviceOrNull(this.VendorID, this.ProductID);

            //HidDeviceLoader device_loader = new HidDeviceLoader();
            //HidDevice device = device_loader.GetDeviceOrDefault(this.VendorID, this.ProductID);

            return device;
        }
    }
}
