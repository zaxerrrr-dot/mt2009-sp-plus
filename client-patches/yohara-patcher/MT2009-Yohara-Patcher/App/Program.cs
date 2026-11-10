using N2_Patcher.Model;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows;

namespace N2_Patcher
{
	// The Yohara patcher's counterpart of the 2.x Program (the shared VPS
	// window uses Program.Title).
	internal static class Program
	{
		public const string Title = "MT2009 PLUS – Yohara Patcher";

		public static string Folder()
		{
			return MT2009Yohara.Entry.Folder;
		}

		public static bool ConfigExists()
		{
			string file = Config.GetConfigFile();
			return !string.IsNullOrEmpty(file) && File.Exists(Path.Combine(Program.Folder(), file));
		}

		public static void Config_EXE()
		{
			if (!Program.ConfigExists())
			{
				MessageBox.Show(string.Concat("Nie znaleziono pliku ", Config.GetConfigFile(), " w folderze klienta."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
				return;
			}
			try
			{
				MT2009Yohara.Entry.StartExternal(Path.Combine(Program.Folder(), Config.GetConfigFile()));
			}
			catch
			{
			}
		}

		public static void newsThread()
		{
			(new Thread(new ThreadStart(N2_Patcher.Control.NewsSystem.loadNews)) { IsBackground = true }).Start();
		}

		public static void Start_EXE()
		{
			string exe = Path.Combine(Program.Folder(), Config.GetStartFile());
			if (!File.Exists(exe))
			{
				MessageBox.Show(string.Concat("Brak pliku ", Config.GetStartFile(), " w folderze klienta Yohara (mógł go usunąć antywirus). Kliknij \"Napraw klienta\", aby go przywrócić, i dodaj folder gry do wyjątków antywirusa."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
				return;
			}
			try
			{
				// the client reads coop.cfg and its packs relative to the working folder;
				// ShellExecute (UAC prompt) - the game exe may need elevation
				MT2009Yohara.Entry.StartExternal(exe);
				MT2009Yohara.PatcherLog.Write("uruchomiono grę: " + exe);
				if (Config.isCLoseOnStart())
				{
					Environment.Exit(0);
				}
			}
			catch (System.ComponentModel.Win32Exception cancelled) when (cancelled.NativeErrorCode == MT2009Yohara.Entry.ErrorCancelled)
			{
				MT2009Yohara.PatcherLog.Write("uruchomienie gry anulowane (UAC)");
				MessageBox.Show("Gra nie została uruchomiona: anulowano zgodę na uprawnienia administratora (UAC). Kliknij GRAJ ponownie i wybierz \"Tak\".", Program.Title, MessageBoxButton.OK, MessageBoxImage.Exclamation);
			}
			catch (Exception exception)
			{
				MT2009Yohara.PatcherLog.Write("nie udało się uruchomić gry: " + exception.Message);
				MessageBox.Show(string.Concat("Nie udało się uruchomić gry:\r\n", exception.Message), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
			}
		}

		public static void URL(string link, string type = null)
		{
			if (!string.IsNullOrEmpty(link))
			{
				try
				{
					Process.Start(new ProcessStartInfo(link) { UseShellExecute = true });
				}
				catch
				{
				}
			}
			else if (type != null)
			{
				MessageBox.Show(string.Concat("Brak wpisu \"", type, "\" w ustawieniach patchera Yohary."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
			}
		}
	}
}
