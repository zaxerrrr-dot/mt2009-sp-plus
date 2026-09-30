using N2_Patcher;
using N2_Patcher.Core;
using N2_Patcher.Model;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace N2_Patcher.Control
{
	internal class DownloadFiles
	{
		private static long patchStarted;

		private static DateTime starttime;

		// MT2009 PLUS: the entry being downloaded and the ones that failed.
		private static PatchItem current;

		private static bool currentIsSelf;

		private static readonly List<PatchItem> failed = new List<PatchItem>();

		public DownloadFiles()
		{
		}

		public static void WC_DownloadFiles()
		{
			FileInfo fileInfo = new FileInfo(Assembly.GetExecutingAssembly().Location);
			MainWindow.BytesNeed = Functions.GetBytesNeed(MainWindow.Patchlist);
			MainWindow.FilesNeed = Functions.GetFilesNeed(MainWindow.Patchlist);
			string clientdata = Config.GetClientdata();
			DownloadFiles.failed.Clear();
			foreach (PatchItem patchlist in MainWindow.Patchlist)
			{
				// The original waited in a busy loop; the same wait, without
				// burning a CPU core.
				while (!MainWindow.IsReady)
				{
					Thread.Sleep(5);
				}
				MainWindow.IsReady = false;
				if (patchlist.Filename.Contains("\\"))
				{
					Directory.CreateDirectory(Functions.GetFolder(string.Concat(Functions.GetCurrentFolder(), patchlist.Filename)));
				}
				DownloadFiles.starttime = DateTime.Now;
				WebClient webClient = new WebClient();
				DownloadFiles.patchStarted = DateTimeOffset.Now.ToUnixTimeMilliseconds();
				webClient.DownloadProgressChanged += new DownloadProgressChangedEventHandler(DownloadFiles.WC_NewDownload_DownloadProgressChanged);
				webClient.DownloadFileCompleted += new AsyncCompletedEventHandler(DownloadFiles.WC_NewDownload_DownloadFileCompleted);
				webClient.Proxy = null;
				DownloadFiles.current = patchlist;
				DownloadFiles.currentIsSelf = false;
				if (string.Equals(fileInfo.Name, patchlist.Filename, StringComparison.OrdinalIgnoreCase))
				{
					// Self-update: a running exe can be renamed, not overwritten.
					string bak = string.Concat(Functions.GetCurrentFolder(), fileInfo.Name, ".bak");
					try
					{
						if (File.Exists(bak))
						{
							File.Delete(bak);
						}
						File.Move(fileInfo.FullName, bak);
						MainWindow.SelfUpgrade = true;
						DownloadFiles.currentIsSelf = true;
					}
					catch (Exception)
					{
						// Cannot replace itself now (no rights): skip, next start tries again.
						DownloadFiles.failed.Add(patchlist);
						DownloadFiles.Finish(patchlist, fileInfo);
						continue;
					}
				}
				try
				{
					webClient.DownloadFileAsync(PatchCore.DownloadUri(clientdata, patchlist), string.Concat(Functions.GetCurrentFolder(), patchlist.Filename));
				}
				catch (Exception)
				{
					DownloadFiles.failed.Add(patchlist);
					DownloadFiles.Finish(patchlist, fileInfo);
				}
			}
		}

		private static void WC_NewDownload_DownloadFileCompleted(object sender, AsyncCompletedEventArgs e)
		{
			FileInfo fileInfo = new FileInfo(Assembly.GetExecutingAssembly().Location);
			PatchItem item = DownloadFiles.current;
			if (e.Error != null || e.Cancelled)
			{
				DownloadFiles.failed.Add(item);
				if (DownloadFiles.currentIsSelf)
				{
					// Put the running patcher back, so the folder keeps a working exe.
					try
					{
						string bak = string.Concat(Functions.GetCurrentFolder(), fileInfo.Name, ".bak");
						if (File.Exists(fileInfo.FullName))
						{
							File.Delete(fileInfo.FullName);
						}
						File.Move(bak, fileInfo.FullName);
					}
					catch (Exception)
					{
					}
					MainWindow.SelfUpgrade = false;
				}
			}
			((WebClient)sender).Dispose();
			DownloadFiles.Finish(item, fileInfo);
		}

		private static void Finish(PatchItem item, FileInfo fileInfo)
		{
			MainWindow.BytesHave += Functions.GetSize(item);
			MainWindow.FilesHave++;
			MainWindow.IsReady = true;
			if (MainWindow.FilesHave == MainWindow.FilesNeed)
			{
				int failedCount = DownloadFiles.failed.Count;
				if (!MainWindow.SelfUpgrade)
				{
					Application.Current.Dispatcher.Invoke(() => {
						MainWindow.WPF.progressBarFileMask.Visibility = Visibility.Hidden;
						MainWindow.WPF.progressBarFileBg.Visibility = Visibility.Hidden;
						MainWindow.WPF.progressBarFile.Visibility = Visibility.Hidden;
						MainWindow.WPF.currentTitle.Visibility = Visibility.Hidden;
						MainWindow.WPF.currentInfo.Visibility = Visibility.Hidden;
						if (failedCount > 0)
						{
							MainWindow.WPF.readyInfo.Text = string.Format("Nie pobrano plików: {0} - uruchom patcher ponownie.", failedCount);
						}
						MainWindow.WPF.readyInfo.Visibility = Visibility.Visible;
						MainWindow.WPF.progressBarFull.Width = 579;
						MainWindow.WPF.ReadyForStart();
					});
				}
				MainWindow.InProgress = false;
				MainWindow.IsPatched = true;
				if (MainWindow.SelfUpgrade)
				{
					Program.SelfUpgrade();
				}
				if (!MainWindow.AutoPatch)
				{
					Program.Start_EXE();
				}
			}
		}

		private static void WC_NewDownload_DownloadProgressChanged(object sender, DownloadProgressChangedEventArgs e)
		{
			bool flag;
			bool flag1;
			long bytesReceived = e.BytesReceived;
			double num = double.Parse(bytesReceived.ToString());
			MainWindow.BytesHaveAtm += num;
			bytesReceived = e.TotalBytesToReceive;
			double num1 = double.Parse(bytesReceived.ToString());
			double num2 = Math.Round(num / num1 * 579, 10);
			double num3 = Math.Round(num / num1 * 100, 0);
			double totalSeconds = (DateTime.Now - DownloadFiles.starttime).TotalSeconds;
			double num4 = num1 / 1024;
			if (num2 > 579 || num2 < 0)
			{
				flag = false;
			}
			else
			{
				flag = (num3 > 579 ? false : num3 >= 0);
			}
			if (flag)
			{
				PatchItem item = DownloadFiles.current;
				Application.Current.Dispatcher.Invoke(() => {
					string[] strArrays = item.Filename.Split(new char[] { '\\' });
					MainWindow.WPF.currentTitle.Text = string.Concat("Pobieranie - ", strArrays[(int)strArrays.Length - 1]);
					MainWindow.WPF.currentInfo.Text = string.Concat(num3.ToString(), "%");
					MainWindow.WPF.progressBarFile.Width = num2;
				});
			}
			bytesReceived = MainWindow.BytesHave + e.BytesReceived;
			double num5 = double.Parse(bytesReceived.ToString());
			double num6 = double.Parse(MainWindow.BytesNeed.ToString());
			double num7 = Math.Round(num5 / num6 * 579, 10);
			double num8 = Math.Round(num5 / num6 * 100, 0);
			long unixTimeMilliseconds = DateTimeOffset.Now.ToUnixTimeMilliseconds();
			if (unixTimeMilliseconds > (long)0)
			{
				double num9 = (double)(unixTimeMilliseconds - DownloadFiles.patchStarted);
				double bytesReceived1 = (double)e.BytesReceived / num9 / 1048.576;
				if (num7 > 579 || num7 < 0)
				{
					flag1 = false;
				}
				else
				{
					flag1 = (num8 > 100 ? false : num8 >= 0);
				}
				if (flag1)
				{
					string.Concat(string.Format("{0:0.0}", bytesReceived1), " Mb/s");
					Application.Current.Dispatcher.Invoke(() => {
						MainWindow.WPF.fullInfo.Text = string.Concat(num8.ToString(), "%");
						MainWindow.WPF.progressBarFull.Width = num7;
					});
				}
			}
			MainWindow.BytesHaveOld = MainWindow.BytesHaveAtm;
		}
	}
}
