using MT2009Yohara;
using MT2009Yohara.Core;
using N2_Patcher.Control;
using N2_Patcher.Core;
using N2_Patcher.Model;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Navigation;
using System.Windows.Threading;

namespace N2_Patcher
{
	// MT2009_PLUS_YOHARA_PATCHER_V1 - the window of the Yohara patcher: the 2.x
	// patcher window (news, server status, VPS window, GRAJ) with the Yohara
	// update (MT2009Yohara.Core.Updater) instead of the 2.x patch list, the
	// version line and "Napraw klienta".
	public partial class MainWindow : Window
	{
		public static MainWindow WPF;

		private const double BarWidth = 579;

		private string _newsLink = "";

		private static readonly Brush OnlineBrush = new SolidColorBrush(Color.FromRgb(0x7C, 0xE3, 0x5A));

		private static readonly Brush OfflineBrush = new SolidColorBrush(Color.FromRgb(0xFF, 0x6A, 0x4D));

		private static readonly Brush CheckingBrush = new SolidColorBrush(Color.FromRgb(0x8F, 0xB8, 0xB2));

		private List<CoopServer> servers = new List<CoopServer>();

		private int serverIndex;

		private int probeGeneration;

		private DispatcherTimer serverTimer;

		private bool updating;

		private bool isYohara;

		public MainWindow()
		{
			this.InitializeComponent();
			MainWindow.WPF = this;
			this.btn_start.IsEnabled = false;
			this.btn_repair.IsEnabled = false;
			if (!Program.ConfigExists())
			{
				this.btn_config.Visibility = Visibility.Collapsed;
				this.btn_vps.Margin = this.btn_config.Margin;
			}
			if (string.IsNullOrEmpty(Config.getVoteForCoins()))
			{
				this.btnVoteForCoins.Visibility = Visibility.Collapsed;
			}
			this.ShowVersion(YoharaClient.ReadStamp(Entry.Folder), null, null);
			PatcherLog.Write("MT2009 PLUS - Yohara Patcher " + typeof(MainWindow).Assembly.GetName().Version + ", folder " + Entry.Folder);

			ClientKind kind = YoharaClient.Detect(Entry.Folder);
			this.isYohara = kind == ClientKind.Yohara;
			if (!this.isYohara)
			{
				// a 2.x client or no client: nothing is checked, nothing downloaded
				string text = kind == ClientKind.Classic2x
					? "To folder klienta 2.x - użyj MT2009-Patcher.exe."
					: "Umieść patcher w folderze klienta Yohara.";
				string detail = kind == ClientKind.Classic2x
					? "Ten folder ma klienta MT2009 PLUS 2.x, nie Yohary.\r\n\r\nDo klienta 2.x służy MT2009-Patcher.exe. MT2009-Yohara-Patcher.exe skopiuj do folderu klienta Yohara (obok metin2client.exe) i uruchom go stamtąd."
					: "W tym folderze nie ma klienta Yohara (brak folderu pack).\r\n\r\nSkopiuj MT2009-Yohara-Patcher.exe do folderu klienta Yohara (obok metin2client.exe) i uruchom go stamtąd.";
				PatcherLog.Write("odmowa: " + kind);
				this.versionInfo.Text = kind == ClientKind.Classic2x ? "To nie jest klient Yohara" : "Brak klienta Yohara";
				this.checkClientTitle.Visibility = Visibility.Hidden;
				this.checkClientInfo.Visibility = Visibility.Hidden;
				this.readyInfo.Text = text;
				this.readyInfo.Visibility = Visibility.Visible;
				this.Loaded += (s, e) => MessageBox.Show(this, detail, Program.Title, MessageBoxButton.OK, MessageBoxImage.Warning);
			}
			Program.newsThread();
			base.DataContext = this;
			new PicWarpper();
			this.ReloadServers(0);
			this.serverTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(20) };
			this.serverTimer.Tick += (s, e) => this.ProbeServer();
			this.serverTimer.Start();
			if (this.isYohara)
			{
				this.Loaded += (s, e) => this.StartUpdate(false);
			}
		}

		// "Klient Yohara 3.0.23 · kanał test"
		private void ShowVersion(string local, string remote, string channel)
		{
			string text = string.IsNullOrEmpty(local) ? "Klient Yohara" : "Klient Yohara " + local;
			if (!string.IsNullOrEmpty(channel))
			{
				text += " · kanał " + channel;
			}
			if (!string.IsNullOrEmpty(remote) && remote != local)
			{
				text += " (na serwerze: " + remote + ")";
			}
			this.versionInfo.Text = text;
		}

		// ------------------------------------------------ update

		private async void StartUpdate(bool full)
		{
			if (this.updating || !this.isYohara)
			{
				return;
			}
			this.updating = true;
			this.btn_start.IsEnabled = false;
			this.btn_repair.IsEnabled = false;
			this.readyInfo.Visibility = Visibility.Hidden;
			this.readyInfo.ToolTip = null;
			this.updateDetail.Text = full ? "Naprawa: sprawdzam sumy SHA-256 wszystkich plików…" : "";
			this.ShowBars(false);
			this.checkClientTitle.Text = "Łączenie z serwerem aktualizacji Yohary…";
			this.checkClientInfo.Text = "";
			this.progressBarFull.Width = 0;
			UpdateOptions options = Entry.Options(full);
			UpdateResult result;
			try
			{
				result = await Task.Run(() => new Updater(new WebHttp(), PatcherLog.Write).Run(options, p =>
					this.Dispatcher.BeginInvoke(new Action(() => this.ShowProgress(p)))));
			}
			catch (Exception exception)
			{
				PatcherLog.Write("błąd: " + exception);
				result = new UpdateResult { State = UpdateState.Failed, Message = "Błąd aktualizacji - możesz grać.", Detail = exception.Message };
			}
			this.updating = false;
			if (result.State == UpdateState.PatcherUpdated)
			{
				try
				{
					Updater.SwapSelf(Entry.ExePath, result.NewPatcherPath);
					PatcherLog.Write("patcher podmieniony na " + result.NewPatcherVersion);
					MessageBox.Show(this, "Patcher Yohary został zaktualizowany (wersja " + result.NewPatcherVersion + ") i uruchomi się ponownie.", Program.Title, MessageBoxButton.OK, MessageBoxImage.Information);
					Entry.Restart(null);
					Environment.Exit(0);
				}
				catch (Exception exception)
				{
					PatcherLog.Write("nie udało się podmienić patchera: " + exception.Message);
					result.State = UpdateState.Partial;
					result.Message = "Nie udało się zaktualizować patchera - pobierz go ponownie.";
				}
			}
			this.Finish(result);
		}

		private void ShowBars(bool downloading)
		{
			Visibility d = downloading ? Visibility.Visible : Visibility.Hidden;
			Visibility c = downloading ? Visibility.Hidden : Visibility.Visible;
			this.checkClientTitle.Visibility = c;
			this.checkClientInfo.Visibility = c;
			this.progressBarFileMask.Visibility = d;
			this.progressBarFileBg.Visibility = d;
			this.progressBarFile.Visibility = d;
			this.currentTitle.Visibility = d;
			this.currentInfo.Visibility = d;
			this.fullTitle.Visibility = d;
			this.fullInfo.Visibility = d;
		}

		private static double Part(double done, double total)
		{
			if (total <= 0)
			{
				return 1;
			}
			return Math.Max(0, Math.Min(1, done / total));
		}

		private void ShowProgress(UpdateProgress p)
		{
			// a report queued just before the end must not cover the result
			if (!this.updating)
			{
				return;
			}
			switch (p.Phase)
			{
				case Phase.Connecting:
					this.ShowBars(false);
					this.checkClientTitle.Text = p.Text;
					break;
				case Phase.Checking:
					{
						this.ShowBars(false);
						double part = Part(p.Done, p.Total);
						this.checkClientTitle.Text = p.Text + ":";
						this.checkClientInfo.Text = Math.Floor(part * 100) + "%";
						this.progressBarFull.Width = BarWidth * part;
						break;
					}
				case Phase.SelfUpdate:
				case Phase.Downloading:
				case Phase.Done:
					{
						this.ShowBars(true);
						string name = p.File ?? "";
						int slash = Math.Max(name.LastIndexOf('/'), name.LastIndexOf('\\'));
						double filePart = Part(p.FileDone, p.FileTotal);
						double allPart = Part(p.BytesDone, p.BytesTotal);
						this.currentTitle.Text = (p.Phase == Phase.SelfUpdate ? "Nowy patcher - " : "Pobieranie - ") + name.Substring(slash + 1);
						this.currentInfo.Text = Math.Floor(filePart * 100) + "%";
						this.progressBarFile.Width = BarWidth * filePart;
						this.fullTitle.Text = string.Format("Postęp całkowity ({0}/{1}, {2:0.0} / {3:0.0} MB)", Math.Min(p.Done + 1, p.Total), p.Total, p.BytesDone / 1048576.0, p.BytesTotal / 1048576.0);
						this.fullInfo.Text = Math.Floor(allPart * 100) + "%";
						this.progressBarFull.Width = BarWidth * allPart;
						break;
					}
			}
		}

		private void Finish(UpdateResult result)
		{
			this.ShowBars(false);
			this.checkClientTitle.Visibility = Visibility.Hidden;
			this.checkClientInfo.Visibility = Visibility.Hidden;
			this.progressBarFull.Width = BarWidth;
			this.readyInfo.Text = result.Message ?? "";
			this.readyInfo.ToolTip = string.IsNullOrEmpty(result.Detail) ? null : result.Detail;
			this.readyInfo.Visibility = Visibility.Visible;
			this.ShowVersion(YoharaClient.ReadStamp(Entry.Folder), result.Version, result.Channel);
			switch (result.State)
			{
				case UpdateState.UpToDate:
				case UpdateState.Updated:
					this.updateDetail.Text = string.Format("Serwer aktualizacji Yohary · sprawdzono {0} plików{1}", result.Checked,
						result.Downloaded > 0 ? string.Format(" · pobrano {0} ({1:0.0} MB)", result.Downloaded, result.Bytes / 1048576.0) : "");
					break;
				case UpdateState.Offline:
					this.updateDetail.Text = "Brak połączenia z serwerem aktualizacji Yohary";
					break;
				default:
					this.updateDetail.Text = result.Detail ?? "";
					break;
			}
			// the game can always be started (as in the 2.x patcher) - even when
			// the server is down or a file failed
			this.btn_start.IsEnabled = this.isYohara;
			this.btn_repair.IsEnabled = this.isYohara;
			if (result.State == UpdateState.Partial || result.State == UpdateState.Failed)
			{
				MessageBox.Show(this, result.Message + (string.IsNullOrEmpty(result.Detail) ? "" : "\r\n\r\n" + result.Detail) +
					"\r\n\r\nSzczegóły: " + PatcherLog.FileName + " w folderze gry.", Program.Title, MessageBoxButton.OK, MessageBoxImage.Warning);
			}
		}

		private void BtnRepair(object sender, MouseButtonEventArgs e)
		{
			if (!this.updating && this.isYohara && this.btn_repair.IsEnabled)
			{
				this.StartUpdate(true);
			}
		}

		// ------------------------------------------------ buttons

		private void BtnClose(object sender, MouseButtonEventArgs e)
		{
			Environment.Exit(0);
		}

		private void WindowClosed(object sender, EventArgs e)
		{
			Environment.Exit(0);
		}

		private void BtnConfig(object sender, MouseButtonEventArgs e)
		{
			Program.Config_EXE();
		}

		private void BtnVps(object sender, MouseButtonEventArgs e)
		{
			VpsWindow dialog = new VpsWindow(Entry.Folder.TrimEnd('\\') + "\\") { Owner = this };
			dialog.ShowDialog();
			this.ReloadServers(dialog.LastSavedSlot);
		}

		private void BtnDiscord(object sender, MouseButtonEventArgs e)
		{
			Program.URL(Config.getDiscord(), "Discord");
		}

		private void BtnHome(object sender, MouseButtonEventArgs e)
		{
			Program.URL(Config.getHomepage(), "Homepage");
		}

		private void BtnMinimize(object sender, MouseButtonEventArgs e)
		{
			base.WindowState = System.Windows.WindowState.Minimized;
		}

		private void btnNextNews(object sender, MouseButtonEventArgs e)
		{
			NewsSystem.next();
		}

		private void btnPrevNews(object sender, MouseButtonEventArgs e)
		{
			NewsSystem.prev();
		}

		private void BtnStartMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
		{
			if (!this.updating && this.isYohara && this.btn_start.IsEnabled)
			{
				Program.Start_EXE();
			}
		}

		private void BtnVoteForCoins(object sender, MouseButtonEventArgs e)
		{
			Program.URL(Config.getVoteForCoins(), "Vote4Coins");
		}

		private void ImgBgMouseLeftDown(object sender, MouseButtonEventArgs e)
		{
			if (e.ButtonState == MouseButtonState.Pressed)
			{
				base.DragMove();
			}
		}

		private void LinkOnRequestNavigate(object sender, RequestNavigateEventArgs e)
		{
			Program.URL(e.Uri.ToString(), null);
		}

		private void newsLink(object sender, MouseButtonEventArgs e)
		{
			Program.URL(this._newsLink, null);
		}

		public void setNewsLink(string url)
		{
			this._newsLink = url;
		}

		// ------------------------------------------------ server status (shared with 2.x: CoopServer, ServerProbe)

		private void BtnServerPrev(object sender, MouseButtonEventArgs e)
		{
			if (this.servers.Count > 1)
			{
				this.serverIndex = (this.serverIndex + this.servers.Count - 1) % this.servers.Count;
				this.ShowServer();
			}
		}

		private void BtnServerNext(object sender, MouseButtonEventArgs e)
		{
			if (this.servers.Count > 1)
			{
				this.serverIndex = (this.serverIndex + 1) % this.servers.Count;
				this.ShowServer();
			}
		}

		private void ReloadServers(int preferSlot)
		{
			int keepSlot = this.servers.Count > 0 ? this.servers[this.serverIndex].Slot : -1;
			this.servers = CoopServer.Discover(Entry.Folder.TrimEnd('\\') + "\\");
			this.serverIndex = 0;
			int wanted = preferSlot > 0 ? preferSlot : keepSlot;
			for (int i = 0; i < this.servers.Count; i++)
			{
				if (this.servers[i].Slot == wanted)
				{
					this.serverIndex = i;
				}
			}
			Visibility arrows = this.servers.Count > 1 ? Visibility.Visible : Visibility.Hidden;
			this.serverPrev.Visibility = arrows;
			this.serverNext.Visibility = arrows;
			this.ShowServer();
		}

		private void ShowServer()
		{
			CoopServer server = this.servers[this.serverIndex];
			this.serverName.Text = server.DisplayName;
			int[] ports = server.ChannelPorts;
			this.serverName.ToolTip = string.Format("{0}  (logowanie {1}, {2})", server.Host, server.Auth,
				string.Join(", ", ports.Select((port, i) => string.Concat("CH", (i + 1).ToString(), " ", port.ToString()))));
			this.SetStatus(null);
			this.ProbeServer();
		}

		private void SetStatus(ChannelState state)
		{
			CoopServer server = this.servers[this.serverIndex];
			this.serverAuth.Inlines.Clear();
			this.serverAuth.Inlines.Add(new Run("Logowanie: "));
			this.serverAuth.Inlines.Add(MainWindow.StateRun(state == null ? (bool?)null : state.auth));
			this.serverChannels.Inlines.Clear();
			this.serverChannels.Inlines.Add(new Run("CH1: "));
			this.serverChannels.Inlines.Add(MainWindow.StateRun(state == null ? (bool?)null : state.channel_1));
			if (server.Channels > 1)
			{
				this.serverChannels.Inlines.Add(new Run("     CH2: "));
				this.serverChannels.Inlines.Add(MainWindow.StateRun(state == null ? (bool?)null : state.channel_2));
			}
			if (server.Channels > 2)
			{
				this.serverChannels.Inlines.Add(new LineBreak());
				this.serverChannels.Inlines.Add(new Run("CH3: "));
				this.serverChannels.Inlines.Add(MainWindow.StateRun(state == null ? (bool?)null : state.channel_3));
			}
			if (server.Channels > 3)
			{
				this.serverChannels.Inlines.Add(new Run("     CH4: "));
				this.serverChannels.Inlines.Add(MainWindow.StateRun(state == null ? (bool?)null : state.channel_4));
			}
		}

		private static Run StateRun(bool? online)
		{
			if (online == null)
			{
				return new Run("...") { Foreground = MainWindow.CheckingBrush };
			}
			return online.Value
				? new Run("ONLINE") { Foreground = MainWindow.OnlineBrush, FontWeight = FontWeights.Bold }
				: new Run("OFFLINE") { Foreground = MainWindow.OfflineBrush, FontWeight = FontWeights.Bold };
		}

		private async void ProbeServer()
		{
			int generation = ++this.probeGeneration;
			CoopServer server = this.servers[this.serverIndex];
			ChannelState state;
			try
			{
				state = await Task.Run(() => ServerProbe.Probe(server, 2000));
			}
			catch
			{
				state = new ChannelState();
			}
			if (generation == this.probeGeneration)
			{
				this.SetStatus(state);
			}
		}
	}
}
