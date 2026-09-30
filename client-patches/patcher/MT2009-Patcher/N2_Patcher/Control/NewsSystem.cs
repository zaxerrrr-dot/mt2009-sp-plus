using N2_Patcher;
using N2_Patcher.Model;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.ComponentModel;
using System.Net;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace N2_Patcher.Control
{
	internal class NewsSystem
	{
		private static string[] newsTypes;

		private static int dotStartX;

		private static int dotEndX;

		private static List<NewsItem> news;

		private static int selected;

		private static int max;

		static NewsSystem()
		{
			NewsSystem.newsTypes = new string[] { "WYDARZENIE", "NOWOŚĆ", "AKTUALIZACJA" };
			NewsSystem.dotStartX = 235;
			NewsSystem.dotEndX = 293;
		}

		public NewsSystem()
		{
		}

		private static bool convertToJson(DownloadStringCompletedEventArgs e)
		{
			bool flag;
			try
			{
				NewsSystem.news = JsonConvert.DeserializeObject<List<NewsItem>>(e.Result);
				flag = true;
			}
			catch (Exception exception) when ((exception is JsonSerializationException ? true : exception is JsonReaderException))
			{
				flag = false;
			}
			return flag;
		}

		private static void downloadCompleted(object sender, DownloadStringCompletedEventArgs e)
		{
			if (e.Error == null)
			{
				if (NewsSystem.convertToJson(e))
				{
					NewsSystem.max = NewsSystem.news.Count;
					if (NewsSystem.max > 0)
					{
						Application.Current.Dispatcher.Invoke(() => {
							if (NewsSystem.max > 1)
							{
								ImageSource bitmapImage = new BitmapImage(new Uri("pack://application:,,,/Resources/dot.png"));
								for (int i = 0; i < NewsSystem.max; i++)
								{
									Image image = new Image()
									{
										Margin = new Thickness((double)(NewsSystem.dotStartX + 12 * i), 268, (double)(NewsSystem.dotEndX - 12 * i), 54),
										Source = bitmapImage
									};
									MainWindow.WPF.Grid.Children.Add(image);
								}
								MainWindow.WPF.activeNewsDot.Visibility = Visibility.Visible;
								MainWindow.WPF.btnNewsPrev.Visibility = Visibility.Visible;
								MainWindow.WPF.btnNewsNext.Visibility = Visibility.Visible;
							}
							MainWindow.WPF.newsBG.Visibility = Visibility.Visible;
							NewsSystem.jumpToNewsStep(0, false);
						});
					}
				}
			}
		}

		private static void jumpToNewsStep(int index, bool onClick)
		{
			Application.Current.Dispatcher.Invoke(() => {
				MainWindow.WPF.activeNewsDot.Margin = new Thickness((double)(NewsSystem.dotStartX + 12 * index), 268, (double)(NewsSystem.dotEndX - 12 * index), 54);
				int type = NewsSystem.news[index].newsType;
				MainWindow.WPF.newsType.Text = NewsSystem.newsTypes[type < 0 || type >= NewsSystem.newsTypes.Length ? 1 : type];
				MainWindow.WPF.newsLinkLable.Visibility = Visibility.Hidden;
				MainWindow.WPF.newsWriter.Text = NewsSystem.news[index].creator;
				// MT2009 PLUS: the Polish type names are longer than EVENT/NEWS/UPDATE;
				// the author starts after the type (at 218 as in the original, or later).
				TextBlock tb = MainWindow.WPF.newsType;
				FormattedText ft = new FormattedText(tb.Text, CultureInfo.CurrentUICulture, FlowDirection.LeftToRight,
					new Typeface(tb.FontFamily, tb.FontStyle, tb.FontWeight, tb.FontStretch), tb.FontSize, Brushes.White,
					VisualTreeHelper.GetDpi(tb).PixelsPerDip);
				MainWindow.WPF.newsWriter.Padding = new Thickness(Math.Max(218, 125 + Math.Ceiling(ft.WidthIncludingTrailingWhitespace) + 10), 41, 125, 0);
				MainWindow.WPF.newsTitle.Text = NewsSystem.news[index].topic;
				if (!string.IsNullOrEmpty(NewsSystem.news[index].threadUrl))
				{
					MainWindow.WPF.newsLinkLable.Visibility = Visibility.Visible;
					MainWindow.WPF.setNewsLink(NewsSystem.news[index].threadUrl);
				}
			});
		}

		public static void loadNews()
		{
			ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;
			ServicePointManager.Expect100Continue = false;
			WebRequest.DefaultWebProxy = null;
			string news = Config.GetNews();
			if (string.IsNullOrEmpty(news))
			{
				return;
			}
			using (WebClient webClient = new WebClient())
			{
				webClient.Proxy = WebRequest.DefaultWebProxy;
				// UTF-8 JSON (Polish letters) even when the server sends no charset.
				webClient.Encoding = System.Text.Encoding.UTF8;
				webClient.DownloadStringCompleted += new DownloadStringCompletedEventHandler(NewsSystem.downloadCompleted);
				webClient.DownloadStringAsync(new Uri(news));
			}
		}

		public static void next()
		{
			NewsSystem.selected++;
			if (NewsSystem.selected >= NewsSystem.max)
			{
				NewsSystem.selected = 0;
			}
			NewsSystem.jumpToNewsStep(NewsSystem.selected, true);
		}

		public static void prev()
		{
			NewsSystem.selected--;
			if (NewsSystem.selected < 0)
			{
				NewsSystem.selected = NewsSystem.max - 1;
			}
			NewsSystem.jumpToNewsStep(NewsSystem.selected, true);
		}
	}
}