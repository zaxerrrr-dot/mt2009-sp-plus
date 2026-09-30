using N2_Patcher.Control;
using N2_Patcher.Core;
using N2_Patcher.Model;
using System;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Navigation;
using System.Windows.Threading;

namespace N2_Patcher
{
	public partial class MainWindow : Window
	{
		public static bool SelfUpgrade;

		public static bool InProgress;

		public static bool AutoPatch;

		public static bool IsPatched;

		// volatile: the download thread waits on it (DownloadFiles).
		public static volatile bool IsReady;

		public static List<PatchItem> Patchlist;

		public static string PatcherHash;

		public static long BytesHave;

		public static long BytesNeed;

		public static int FilesHave;

		public static int FilesNeed;

		public static double BytesHaveOld;

		public static double BytesHaveAtm;

		public static string news1;

		public static string news2;

		public static string news3;

		public static MainWindow WPF;

		private string _newsLink = "";

		// MT2009 PLUS: server status (see ServerProbe).
		private static readonly Brush OnlineBrush = new SolidColorBrush(Color.FromRgb(0x7C, 0xE3, 0x5A));

		private static readonly Brush OfflineBrush = new SolidColorBrush(Color.FromRgb(0xFF, 0x6A, 0x4D));

		private static readonly Brush CheckingBrush = new SolidColorBrush(Color.FromRgb(0xB0, 0xA0, 0x90));

		private List<CoopServer> servers = new List<CoopServer>();

		private int serverIndex;

		private int probeGeneration;

		private DispatcherTimer serverTimer;

		public MainWindow()
		{
			Functions.ClearOldVersion();
			this.InitializeComponent();
			MainWindow.AutoPatch = true;
			MainWindow.WPF = this;
			MainWindow.WPF.btn_start.IsEnabled = false;
			// The gear starts the client's config program; without one it is hidden
			// and the VPS button takes its place.
			if (!Program.ConfigExists())
			{
				this.btn_config.Visibility = Visibility.Collapsed;
				this.btn_vps.Margin = this.btn_config.Margin;
			}
			if (string.IsNullOrEmpty(Config.getVoteForCoins()))
			{
				this.btnVoteForCoins.Visibility = Visibility.Collapsed;
			}
			// MT2009 PLUS: the patch list is an update of an installed client (packs,
			// metin2client.exe), not a whole client - outside a client folder it
			// would only fill the folder with files that cannot run.
			if (System.IO.Directory.Exists(string.Concat(Functions.GetCurrentFolder(), "pack")))
			{
				Program.Patchlist_Thread();
			}
			else
			{
				this.readyInfo.Text = "Umieść patcher w folderze gry (obok metin2client.exe).";
				this.readyInfo.Visibility = Visibility.Visible;
				this.Loaded += (s, e) => MessageBox.Show(this,
					"W tym folderze nie ma klienta MT2009 (brak folderu pack).\r\n\r\nSkopiuj MT2009-Patcher.exe (i MT2009-Patcher.exe.config) do folderu gry, obok metin2client.exe, i uruchom go stamtąd.",
					Program.Title, MessageBoxButton.OK, MessageBoxImage.Warning);
			}
			Program.newsThread();
			base.DataContext = this;
			PicWarpper picWarpper = new PicWarpper();
			this.ReloadServers(0);
			this.serverTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(20) };
			this.serverTimer.Tick += (s, e) => this.ProbeServer();
			this.serverTimer.Start();
		}

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
			VpsWindow dialog = new VpsWindow(Functions.GetCurrentFolder()) { Owner = this };
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
			if (!MainWindow.InProgress)
			{
				if (!MainWindow.AutoPatch)
				{
					Program.Patchlist_Thread();
				}
				else
				{
					Program.Start_EXE();
				}
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

		public void ReadyForStart()
		{
			MainWindow.WPF.btn_start.IsEnabled = true;
		}

		public void setNewsLink(string url)
		{
			this._newsLink = url;
		}

		// ------------------------------------------------ server status

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

		// preferSlot: 1/2 = show that coop file's server if valid, 0 = keep.
		private void ReloadServers(int preferSlot)
		{
			int keepSlot = this.servers.Count > 0 ? this.servers[this.serverIndex].Slot : -1;
			this.servers = CoopServer.Discover(Functions.GetCurrentFolder());
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
			this.serverName.ToolTip = string.Format("{0}  (logowanie {1}, CH1 {2}{3})", server.Host, server.Auth, server.Channel,
				server.Channels > 1 ? string.Concat(", CH2 ", (server.Channel + 10).ToString()) : "");
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
			// A newer probe (another server chosen) wins.
			if (generation == this.probeGeneration)
			{
				this.SetStatus(state);
			}
		}
	}
}
