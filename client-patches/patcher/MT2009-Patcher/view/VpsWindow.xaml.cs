using N2_Patcher.Core;
using System;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Input;

namespace N2_Patcher
{
	// MT2009 PLUS: two slots of the game's server list - coop.cfg (1) and
	// coop2.cfg (2) - shown, added, corrected and removed like in
	// MT2009-Aktualizator (Show-AktServerDialog). Validation: CoopServer.
	public partial class VpsWindow : Window
	{
		private readonly string root;

		private bool loading;

		// The slot saved last (0 = nothing saved), so the main window shows it.
		public int LastSavedSlot { get; private set; }

		public VpsWindow(string clientFolder)
		{
			this.root = clientFolder;
			this.InitializeComponent();
			this.Refresh();
			// The first empty slot, so adding a second server does not replace the first.
			if (CoopServer.Read(CoopServer.PathFor(this.root, 1), 1) != null && CoopServer.Read(CoopServer.PathFor(this.root, 2), 2) == null)
			{
				this.radio2.IsChecked = true;
			}
			else
			{
				this.radio1.IsChecked = true;
			}
			this.Load();
		}

		private int Slot
		{
			get { return this.radio2.IsChecked == true ? 2 : 1; }
		}

		private string Describe(int slot)
		{
			string file = CoopServer.FileName(slot);
			CoopServer config = CoopServer.Read(CoopServer.PathFor(this.root, slot), slot);
			if (config == null)
			{
				return string.Format("Miejsce {0} ({1}): puste", slot, file);
			}
			if (!config.Valid)
			{
				return string.Format("Miejsce {0} ({1}): plik uszkodzony - gra go pomija", slot, file);
			}
			return string.Format("Miejsce {0} ({1}): {2} - {3}", slot, file, config.Name, config.Host);
		}

		private void Refresh()
		{
			this.radio1.Content = this.Describe(1);
			this.radio2.Content = this.Describe(2);
		}

		private void Load()
		{
			this.loading = true;
			CoopServer config = CoopServer.Read(CoopServer.PathFor(this.root, this.Slot), this.Slot);
			if (config == null)
			{
				this.txtName.Text = "";
				this.txtHost.Text = "";
				this.txtAuth.Text = CoopServer.DefaultAuth.ToString();
				this.txtChannel.Text = CoopServer.DefaultChannel.ToString();
				this.channels2.IsChecked = true;
			}
			else
			{
				this.txtName.Text = config.Name;
				this.txtHost.Text = config.Host;
				this.txtAuth.Text = config.Auth.ToString();
				this.txtChannel.Text = config.Channel.ToString();
				if (config.Channels == 1)
				{
					this.channels1.IsChecked = true;
				}
				else
				{
					this.channels2.IsChecked = true;
				}
			}
			this.btnRemove.IsEnabled = config != null;
			this.loading = false;
		}

		private void SlotChanged(object sender, RoutedEventArgs e)
		{
			if (this.txtName != null && !this.loading)
			{
				this.Load();
			}
		}

		private MessageBoxResult Ask(string text)
		{
			return MessageBox.Show(this, text, Program.Title, MessageBoxButton.YesNo, MessageBoxImage.Question);
		}

		private void SaveClick(object sender, RoutedEventArgs e)
		{
			int slot = this.Slot;
			CoopServer config;
			try
			{
				config = CoopServer.Create(this.txtName.Text, this.txtHost.Text, this.txtAuth.Text, this.txtChannel.Text, this.channels1.IsChecked == true ? "1" : "2");
			}
			catch (CoopException exception)
			{
				MessageBox.Show(this, exception.Message, Program.Title, MessageBoxButton.OK, MessageBoxImage.Warning);
				return;
			}
			CoopServer existing = CoopServer.Read(CoopServer.PathFor(this.root, slot), slot);
			if (existing != null && existing.Valid && (existing.Host != config.Host || existing.Name != config.Name))
			{
				if (this.Ask(string.Format("W miejscu {0} jest już serwer \"{1}\" ({2}). Zastąpić go?", slot, existing.Name, existing.Host)) != MessageBoxResult.Yes)
				{
					return;
				}
			}
			try
			{
				CoopServer.Save(this.root, slot, config);
			}
			catch (Exception exception)
			{
				MessageBox.Show(this, string.Concat("Nie udało się zapisać pliku ", CoopServer.FileName(slot), ":\r\n", exception.Message,
					"\r\n\r\nFolder gry w Program Files albo blokada antywirusa? Przenieś klienta np. do C:\\Gry."), Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
				return;
			}
			this.LastSavedSlot = slot;
			this.Refresh();
			this.Load();
			string channelsText = config.Channels == 2 ? "CH1 i CH2" : "CH1";
			string running = VpsWindow.IsGameRunning(this.root) ? "\r\n\r\nGra jest uruchomiona - serwer pojawi się po jej ponownym uruchomieniu." : "";
			MessageBox.Show(this, string.Format("Zapisano.\r\n\r\nW grze wybierz serwer \"Online: {0}\" ({1}).{2}", config.Name, channelsText, running), Program.Title, MessageBoxButton.OK, MessageBoxImage.Information);
		}

		private void RemoveClick(object sender, RoutedEventArgs e)
		{
			int slot = this.Slot;
			if (this.Ask(string.Format("Usunąć serwer z miejsca {0}?", slot)) != MessageBoxResult.Yes)
			{
				return;
			}
			try
			{
				CoopServer.Remove(this.root, slot);
			}
			catch (Exception exception)
			{
				MessageBox.Show(this, exception.Message, Program.Title, MessageBoxButton.OK, MessageBoxImage.Hand);
				return;
			}
			this.Refresh();
			this.Load();
		}

		// metin2client started from this client folder.
		private static bool IsGameRunning(string root)
		{
			string folder = Path.GetFullPath(root).TrimEnd('\\');
			foreach (Process process in Process.GetProcessesByName("metin2client"))
			{
				try
				{
					string dir = Path.GetDirectoryName(process.MainModule.FileName);
					if (string.Equals(dir, folder, StringComparison.OrdinalIgnoreCase))
					{
						return true;
					}
				}
				catch
				{
					// No access to the path: count it as this game.
					return true;
				}
			}
			return false;
		}

		private void TitleMouseDown(object sender, MouseButtonEventArgs e)
		{
			if (e.ButtonState == MouseButtonState.Pressed)
			{
				this.DragMove();
			}
		}

		private void CloseClick(object sender, MouseButtonEventArgs e)
		{
			this.Close();
		}

		private void CloseButtonClick(object sender, RoutedEventArgs e)
		{
			this.Close();
		}
	}
}
