using N2_Patcher;
using N2_Patcher.Core;
using N2_Patcher.Model;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace N2_Patcher.Control
{
	internal class CreatePatchlist
	{
		public CreatePatchlist()
		{
		}

		public static void WC_DownloadPatchlist()
		{
			ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
			ServicePointManager.Expect100Continue = false;
			WebRequest.DefaultWebProxy = null;
			MainWindow.InProgress = true;
			using (WebClient webClient = new WebClient())
			{
				webClient.Proxy = WebRequest.DefaultWebProxy;
				// UTF-8 JSON (Polish letters) even when the server sends no charset.
				webClient.Encoding = System.Text.Encoding.UTF8;
				webClient.Headers.Add("user-agent", Config.getUserAgent());
				webClient.DownloadStringCompleted += new DownloadStringCompletedEventHandler(CreatePatchlist.WC_NewDownload_DownloadstringCompleted);
				webClient.DownloadStringAsync(new Uri(Config.GetPatchlist()));
			}
		}

		private static async void WC_NewDownload_DownloadstringCompleted(object sender, DownloadStringCompletedEventArgs e)
		{
			// MT2009 PLUS: a list that is not valid JSON counts as "no server"
			// (the original crashed on it).
			List<PatchItem> patchItems = null;
			if (e.Error == null)
			{
				try
				{
					patchItems = PatchCore.ParsePatchlist(e.Result);
				}
				catch (Exception)
				{
					patchItems = null;
				}
			}
			if (patchItems == null)
			{
				Dispatcher dispatcher = Application.Current.Dispatcher;
				dispatcher.Invoke(() => {
					MainWindow.WPF.readyInfo.Text = "Serwer aktualizacji niedostępny - możesz grać.";
					MainWindow.WPF.readyInfo.Visibility = Visibility.Visible;
					MainWindow.WPF.checkClientInfo.Text = "100%";
					MainWindow.WPF.progressBarFull.Width = 579;
					MainWindow.InProgress = false;
					MainWindow.IsPatched = true;
					MainWindow.WPF.ReadyForStart();
				});
			}
			else
			{
				MainWindow.FilesHave = 0;
				MainWindow.FilesNeed = patchItems.Count;
				SplitList splitList = new SplitList(patchItems);
				List<PatchItem> patchlist = await Functions.GetPatchlist(splitList.List1);
				List<PatchItem> list = patchlist;
				patchlist = null;
				List<PatchItem> patchlist1 = await Functions.GetPatchlist(splitList.List2);
				List<PatchItem> list1 = patchlist1;
				patchlist1 = null;
				List<PatchItem> patchItems1 = await Functions.GetPatchlist(splitList.List3);
				List<PatchItem> patchItems2 = patchItems1;
				patchItems1 = null;
				List<PatchItem> patchlist2 = await Functions.GetPatchlist(splitList.List4);
				List<PatchItem> patchItems3 = patchlist2;
				patchlist2 = null;
				List<PatchItem> patchlist3 = await Functions.GetPatchlist(splitList.List5);
				List<PatchItem> patchItems4 = patchlist3;
				patchlist3 = null;
				List<PatchItem> patchlist4 = await Functions.GetPatchlist(splitList.List6);
				List<PatchItem> patchItems5 = patchlist4;
				patchlist4 = null;
				List<PatchItem> patchlist5 = await Functions.GetPatchlist(splitList.List7);
				List<PatchItem> patchItems6 = patchlist5;
				patchlist5 = null;
				List<PatchItem> patchlist6 = await Functions.GetPatchlist(splitList.List8);
				List<PatchItem> patchItems7 = patchlist6;
				patchlist6 = null;
				list = list.Concat<PatchItem>(list1).Concat<PatchItem>(patchItems2).Concat<PatchItem>(patchItems3).ToList<PatchItem>();
				list1 = patchItems4.Concat<PatchItem>(patchItems5).Concat<PatchItem>(patchItems6).Concat<PatchItem>(patchItems7).ToList<PatchItem>();
				MainWindow.Patchlist = list.Concat<PatchItem>(list1).ToList<PatchItem>();
				MainWindow.IsReady = true;
				MainWindow.BytesHave = (long)0;
				MainWindow.BytesNeed = (long)0;
				MainWindow.FilesHave = 0;
				MainWindow.FilesNeed = 0;
				DateTime now = DateTime.Now;
				DateTime dateTime = DateTime.Now;
				if (MainWindow.Patchlist.Count <= 0)
				{
					MainWindow.InProgress = false;
					MainWindow.IsPatched = true;
					Dispatcher dispatcher1 = Application.Current.Dispatcher;
					dispatcher1.Invoke(() => {
						MainWindow.WPF.readyInfo.Visibility = Visibility.Visible;
						MainWindow.WPF.checkClientInfo.Text = "100%";
						MainWindow.WPF.progressBarFull.Width = 579;
						MainWindow.WPF.ReadyForStart();
					});
					if (!MainWindow.AutoPatch)
					{
						Program.Start_EXE();
					}
				}
				else
				{
					Dispatcher dispatcher2 = Application.Current.Dispatcher;
					dispatcher2.Invoke(() => {
						MainWindow.WPF.checkClientTitle.Visibility = Visibility.Hidden;
						MainWindow.WPF.checkClientInfo.Visibility = Visibility.Hidden;
						MainWindow.WPF.progressBarFileMask.Visibility = Visibility.Visible;
						MainWindow.WPF.progressBarFileBg.Visibility = Visibility.Visible;
						MainWindow.WPF.currentTitle.Visibility = Visibility.Visible;
						MainWindow.WPF.currentInfo.Visibility = Visibility.Visible;
						MainWindow.WPF.fullTitle.Visibility = Visibility.Visible;
						MainWindow.WPF.fullInfo.Visibility = Visibility.Visible;
					});
					Program.Files_Thread();
				}
				patchItems = null;
				splitList = null;
				list = null;
				list1 = null;
				patchItems2 = null;
				patchItems3 = null;
				patchItems4 = null;
				patchItems5 = null;
				patchItems6 = null;
				patchItems7 = null;
			}
		}
	}
}