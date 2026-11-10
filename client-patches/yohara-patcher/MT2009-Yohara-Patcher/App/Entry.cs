using MT2009Yohara.Core;
using N2_Patcher.Model;
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace MT2009Yohara
{
	// MT2009_PLUS_YOHARA_PATCHER_V1 - entry point.
	//
	//   MT2009-Yohara-Patcher.exe                      the window
	//   MT2009-Yohara-Patcher.exe --cli [--napraw] [--kanal test|stable] [--serwer URL] [--folder DIR]
	//                             [--bez-samoaktualizacji] [--graj]
	//                                                  without a window (tests, advanced players):
	//                                                  exit code 0 = up to date / updated, 1 = error,
	//                                                  2 = not a Yohara folder, 3 = patcher updated (run again)
	//   --kanal / --serwer also work with the window.
	public static class Entry
	{
		public const string AfterUpdateArgument = "--yohara-po-aktualizacji";

		public static string Folder;

		public static string ExePath;

		private static Mutex mutex;

		private static string Snapshot;

		private static int SnapshotDelay = 10;

		[STAThread]
		public static int Main(string[] args)
		{
			Embedded.Install();
			ExePath = Assembly.GetExecutingAssembly().Location;
			Folder = Path.GetDirectoryName(ExePath);
			bool cli = false;
			for (int i = 0; i < args.Length; i++)
			{
				switch (args[i])
				{
					case "--cli": cli = true; break;
					case "--kanal": if (i + 1 < args.Length) Config.ChannelOverride = args[++i]; break;
					case "--serwer": if (i + 1 < args.Length) Config.MirrorOverride = args[++i]; break;
					case "--folder": if (i + 1 < args.Length) Folder = Path.GetFullPath(args[++i]); break;
					case "--zrzut":
						if (i + 1 < args.Length) Snapshot = Path.GetFullPath(args[++i]);
						int delay;
						if (i + 1 < args.Length && int.TryParse(args[i + 1], out delay)) { SnapshotDelay = delay; i++; }
						break;
				}
			}
			// The patcher works on the folder it lies in (a shortcut may start
			// it with another working folder).
			try
			{
				Directory.SetCurrentDirectory(Folder);
			}
			catch
			{
			}
			PatcherLog.Folder = Folder;
			// After a self-update: wait until the old patcher has ended.
			for (int i = 0; i + 1 < args.Length; i++)
			{
				int pid;
				if (args[i] == AfterUpdateArgument && int.TryParse(args[i + 1], out pid))
				{
					try
					{
						Process.GetProcessById(pid).WaitForExit(15000);
					}
					catch
					{
					}
				}
			}
			Updater.CleanupOldSelf(ExePath);
			// one Yohara patcher per client folder (the 2.x patcher checks its own
			// process name "MT2009-Patcher"; the two never block each other)
			bool first;
			mutex = new Mutex(true, MutexName(Folder), out first);
			if (!first)
			{
				PatcherLog.Write("patcher Yohary już działa w tym folderze - koniec");
				return cli ? 1 : 0;
			}
			try
			{
				return cli ? Cli.Run(args) : RunWindow();
			}
			finally
			{
				try
				{
					mutex.ReleaseMutex();
				}
				catch
				{
				}
			}
		}

		public static string MutexName(string folder)
		{
			using (SHA1 sha = SHA1.Create())
			{
				byte[] hash = sha.ComputeHash(Encoding.UTF8.GetBytes(folder.TrimEnd('\\', '/').ToLowerInvariant()));
				return "Local\\MT2009PLUS-Yohara-Patcher-" + BitConverter.ToString(hash, 0, 8).Replace("-", "");
			}
		}

		// kept out of Main, so "--cli" never loads WPF
		[MethodImpl(MethodImplOptions.NoInlining)]
		private static int RunWindow()
		{
			N2_Patcher.App app = new N2_Patcher.App();
			app.InitializeComponent();
			// the window is made inside Run (as with StartupUri in the 2.x
			// patcher): its async code needs the dispatcher's
			// SynchronizationContext, which exists only from there on
			app.Startup += (s, e) => {
				N2_Patcher.MainWindow window = new N2_Patcher.MainWindow();
				app.MainWindow = window;
				window.Show();
				if (!string.IsNullOrEmpty(Snapshot))
				{
					// "--zrzut plik.png [sekundy]": a picture of the window (Wine/Xvfb tests,
					// where a transparent window is not drawn on screen)
					System.Windows.Threading.DispatcherTimer timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromSeconds(SnapshotDelay) };
					timer.Tick += (s2, e2) => {
						timer.Stop();
						try
						{
							System.Windows.FrameworkElement root = (System.Windows.FrameworkElement)window.Content;
							System.Windows.Media.Imaging.RenderTargetBitmap bitmap = new System.Windows.Media.Imaging.RenderTargetBitmap(
								(int)root.ActualWidth, (int)root.ActualHeight, 96, 96, System.Windows.Media.PixelFormats.Pbgra32);
							bitmap.Render(root);
							System.Windows.Media.Imaging.PngBitmapEncoder png = new System.Windows.Media.Imaging.PngBitmapEncoder();
							png.Frames.Add(System.Windows.Media.Imaging.BitmapFrame.Create(bitmap));
							using (FileStream file = File.Create(Snapshot))
							{
								png.Save(file);
							}
						}
						catch (Exception exception)
						{
							PatcherLog.Write("zrzut: " + exception);
						}
						Environment.Exit(0);
					};
					timer.Start();
				}
			};
			return app.Run();
		}

		// Starts the (new) patcher again after a self-update; the new one waits
		// for this process to end.
		public static void Restart(string extra)
		{
			ProcessStartInfo info = new ProcessStartInfo(ExePath)
			{
				Arguments = string.Concat(AfterUpdateArgument, " ", Process.GetCurrentProcess().Id.ToString(), extra ?? ""),
				WorkingDirectory = Folder,
				UseShellExecute = false
			};
			Process.Start(info);
		}

		public static UpdateOptions Options(bool full)
		{
			return new UpdateOptions
			{
				Root = Folder,
				MirrorUrl = Config.GetMirror(),
				Channel = Config.GetChannel(),
				FullVerify = full,
				SelfPath = ExePath
			};
		}
	}
}
