using N2_Patcher.Control;
using N2_Patcher.Model;
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Threading;
using System.Windows;

namespace N2_Patcher
{
	internal class Program
	{
		public const string Title = "MT2009 PLUS Patcher";

		// Passed to the new exe after a self-update: it waits for the old one to end.
		public const string AfterUpdateArgument = "--po-aktualizacji";

		public Program()
		{
		}

		public static bool ConfigExists()
		{
			string file = Config.GetConfigFile();
			return !string.IsNullOrEmpty(file) && File.Exists(string.Concat(Functions.GetCurrentFolder(), file));
		}

		public static void Config_EXE()
		{
			if (!Program.ConfigExists())
			{
				MessageBox.Show(string.Concat("Nie znaleziono pliku ", Config.GetConfigFile(), " w folderze klienta."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
			}
			else
			{
				try
				{
					Process process = new Process();
					process.StartInfo.FileName = string.Concat(Functions.GetCurrentFolder(), Config.GetConfigFile());
					process.StartInfo.WorkingDirectory = Functions.GetCurrentFolder();
					process.Start();
				}
				catch
				{
					return;
				}
			}
		}

		public static void Files_Thread()
		{
			(new Thread(new ThreadStart(DownloadFiles.WC_DownloadFiles)) { IsBackground = true }).Start();
		}

		public static void newsThread()
		{
			(new Thread(new ThreadStart(NewsSystem.loadNews)) { IsBackground = true }).Start();
		}

		public static void Patchlist_Thread()
		{
			(new Thread(new ThreadStart(CreatePatchlist.WC_DownloadPatchlist)) { IsBackground = true }).Start();
		}

		public static void Self()
		{
			Process.Start(Assembly.GetExecutingAssembly().Location);
		}

		// MT2009 PLUS: the original started an external updater ("Update" in
		// the config). The new exe is already in place (the old one was renamed
		// to .bak), so the patcher simply starts it and ends; the new one waits
		// for this process, then deletes the .bak (Functions.ClearOldVersion).
		public static void SelfUpgrade()
		{
			string str1 = Program.Title;
			MessageBox.Show("Patcher został zaktualizowany i uruchomi się ponownie.", str1, MessageBoxButton.OK);
			try
			{
				string exe = Assembly.GetExecutingAssembly().Location;
				int id = Process.GetCurrentProcess().Id;
				ProcessStartInfo processStartInfo = new ProcessStartInfo(exe)
				{
					Arguments = string.Concat(Program.AfterUpdateArgument, " ", id.ToString()),
					WorkingDirectory = Functions.GetCurrentFolder(),
					UseShellExecute = false
				};
				Process.Start(processStartInfo);
				Environment.Exit(0);
			}
			catch
			{
				MessageBox.Show("Nie udało się ponownie uruchomić patchera. Uruchom go jeszcze raz ręcznie.", str1, MessageBoxButton.OK);
				Environment.Exit(0);
			}
		}

		public static void Start_EXE()
		{
			if (!File.Exists(string.Concat(Functions.GetCurrentFolder(), Config.GetStartFile())))
			{
				MessageBox.Show(string.Concat("Brak pliku ", Config.GetStartFile(), " w folderze klienta (mógł go usunąć antywirus). Uruchom patcher ponownie, aby go przywrócić, i dodaj folder gry do wyjątków antywirusa."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
			}
			else
			{
				try
				{
					Process process = new Process();
					process.StartInfo.FileName = string.Concat(Functions.GetCurrentFolder(), Config.GetStartFile());
					// The client reads coop.cfg and its packs relative to the working folder.
					process.StartInfo.WorkingDirectory = Functions.GetCurrentFolder();
					if (Config.isStartToken())
					{
						// The original's launcher token: MD5(key + year-day-hour), lower case.
						DateTime now = DateTime.Now;
						string privateKey = Config.getPrivateKey();
						string[] str = new string[] { privateKey, null, null, null, null, null };
						int year = now.Year;
						str[1] = year.ToString();
						str[2] = "-";
						year = now.Day;
						str[3] = year.ToString();
						str[4] = "-";
						year = now.Hour;
						str[5] = year.ToString();
						string str1 = string.Concat(str);
						process.StartInfo.Arguments = Functions.CreateMD5Hash(str1).ToLower();
					}
					process.Start();
					if (Config.isCLoseOnStart())
					{
						Environment.Exit(0);
					}
				}
				catch (Exception exception)
				{
					MessageBox.Show(string.Concat("Nie udało się uruchomić gry:\r\n", exception.Message), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
					return;
				}
			}
		}

		public static void URL(string Link, string type = null)
		{
			if ((Link == null ? false : Link != ""))
			{
				try
				{
					Process.Start(new ProcessStartInfo(Link) { UseShellExecute = true });
				}
				catch
				{
				}
			}
			else if (type != null)
			{
				MessageBox.Show(string.Concat("Brak wpisu \"", type, "\" w pliku ustawień patchera."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
			}
		}
	}
}
