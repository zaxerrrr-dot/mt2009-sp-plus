using N2_Patcher;
using System;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace N2_Patcher.Control
{
	internal class PicWarpper
	{
		public PicWarpper()
		{
			(new Thread(new ThreadStart(this.Init)) { IsBackground = true }).Start();
		}

		private static BitmapImage Load(int index)
		{
			BitmapImage image = new BitmapImage();
			image.BeginInit();
			image.UriSource = new Uri(string.Concat("pack://application:,,,/resources/animate/bg_", string.Format("{0:00000}", index), ".png"));
			image.CacheOption = BitmapCacheOption.OnLoad;
			image.EndInit();
			image.Freeze();
			return image;
		}

		public void Init()
		{
			int num = 16;
			int num1 = 0;
			int num2 = 95;
			int num3 = num1;
			while (true)
			{
				if (num3 > num2)
				{
					num3 = num1;
				}
				// MT2009 PLUS: each frame is decoded here, on this thread (the
				// original decoded it inside Dispatcher.Invoke, on the UI thread).
				// No cache on purpose: 96 decoded frames would take ~190 MB.
				BitmapImage frame;
				try
				{
					frame = PicWarpper.Load(num3);
				}
				catch
				{
					return;
				}
				try
				{
					Application.Current.Dispatcher.Invoke(() => MainWindow.WPF.animanteBg.Source = frame);
				}
				catch
				{
					return;
				}
				Thread.Sleep(num);
				num3++;
			}
		}
	}
}
