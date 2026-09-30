using N2_Patcher;
using N2_Patcher.Core;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace N2_Patcher.Model
{
	internal class Functions
	{
		public Functions()
		{
		}

		public static string CleanText(string text)
		{
			if (text.Substring(0, 1) == "\n")
			{
			}
			text = text.Substring(1, text.Length - 1);
			string[] strArrays = text.Split("\n".ToCharArray());
			string str = "";
			for (int i = 1; i < strArrays.Count<string>(); i++)
			{
				if (strArrays[i] != "")
				{
					str = string.Concat(str, strArrays[i], " ");
				}
			}
			str = str.Replace("  ", " ");
			string str1 = string.Concat(strArrays[0], Environment.NewLine, str);
			return str1;
		}

		public static bool ClearOldVersion()
		{
			bool flag;
			FileInfo fileInfo = new FileInfo(Assembly.GetExecutingAssembly().Location);
			string str = string.Concat(fileInfo.Name, ".bak");
			if (File.Exists(string.Concat(Functions.GetCurrentFolder(), str)))
			{
				try
				{
					File.Delete(string.Concat(Functions.GetCurrentFolder(), str));
				}
				catch (Exception)
				{
					flag = false;
					return flag;
				}
			}
			flag = true;
			return flag;
		}

		public static string CreateMD5Hash(string input)
		{
			MD5 mD5 = MD5.Create();
			byte[] bytes = Encoding.ASCII.GetBytes(input);
			byte[] numArray = mD5.ComputeHash(bytes);
			StringBuilder stringBuilder = new StringBuilder();
			for (int i = 0; i < (int)numArray.Length; i++)
			{
				stringBuilder.Append(numArray[i].ToString("X2"));
			}
			return stringBuilder.ToString();
		}

		public static long GetBytesNeed(List<PatchItem> Patchlist)
		{
			long num;
			try
			{
				long filesize = (long)0;
				foreach (PatchItem patchlist in Patchlist)
				{
					filesize += patchlist.Filesize;
				}
				num = filesize;
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetBytesNeed Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				num = (long)0;
			}
			return num;
		}

		public static string GetCurrentFolder()
		{
			string str;
			try
			{
				str = string.Concat(Directory.GetCurrentDirectory(), "\\");
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetCurrentFolder Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				str = "";
			}
			return str;
		}

		public static int GetFilesNeed(List<PatchItem> Patchlist)
		{
			int count;
			try
			{
				count = Patchlist.Count;
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetFilesNeed Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				count = 0;
			}
			return count;
		}

		public static string GetFolder(string Line)
		{
			string str;
			try
			{
				str = PatchCore.GetFolder(Line);
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetFolder Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				str = "";
			}
			return str;
		}

		public static string GetMD5(string File_Name)
		{
			string str;
			try
			{
				str = PatchCore.GetMD5(File_Name);
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(Functions.FileErrorText(File_Name, exception), "MT2009 PLUS Patcher", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				str = "";
			}
			return str;
		}

		public static async Task<List<PatchItem>> GetPatchlist(List<PatchItem> patchlist)
		{
			List<PatchItem> patchItems;
			try
			{
				patchItems = PatchCore.SelectForDownload(patchlist, Functions.GetCurrentFolder(), () => Functions.UpdateState("Sprawdzanie plików klienta"));
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(Functions.FileErrorText(null, exception), "MT2009 PLUS Patcher", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				patchItems = new List<PatchItem>();
			}
			await Task.CompletedTask;
			return patchItems;
		}

		// MT2009 PLUS: a Polish sentence instead of a stack trace for the usual
		// causes (game running, antivirus, no write access).
		public static string FileErrorText(string file, Exception exception)
		{
			string name = file == null ? "" : string.Concat(" (", Path.GetFileName(file), ")");
			if (exception is UnauthorizedAccessException)
			{
				return string.Concat("Brak dostępu do pliku klienta", name, ".\r\n\r\nPrawdopodobnie folder gry jest w Program Files albo blokuje go antywirus / ochrona folderów. Przenieś klienta np. do C:\\Gry albo uruchom patcher jako administrator.\r\n\r\n", exception.Message);
			}
			if (exception is IOException)
			{
				return string.Concat("Plik klienta jest w użyciu albo nie można go odczytać", name, ".\r\n\r\nZamknij grę (metin2client.exe) i uruchom patcher ponownie. Jeśli to nie pomoże, dodaj folder gry do wyjątków antywirusa.\r\n\r\n", exception.Message);
			}
			return string.Concat("Błąd patchera", name, ":\r\n\r\n", exception.ToString());
		}

		public static long GetSize(PatchItem item)
		{
			long filesize;
			try
			{
				filesize = item.Filesize;
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetSize Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				filesize = (long)0;
			}
			return filesize;
		}

		public static string GetstringReplaced(string String, string Replace1, string Replace2)
		{
			string str;
			try
			{
				while (String.Contains(Replace1))
				{
					String = String.Replace(Replace1, Replace2);
				}
				str = String;
			}
			catch (Exception exception1)
			{
				Exception exception = exception1;
				MessageBox.Show(exception.ToString(), "GetstringReplaced Error", MessageBoxButton.OK, MessageBoxImage.Hand);
				Environment.Exit(0);
				str = "";
			}
			return str;
		}

		public static IEnumerable<List<T>> SplitList<T>(List<T> bigList, int nSize = 3)
		{
			for (int i = 0; i < bigList.Count; i += nSize)
			{
				yield return bigList.GetRange(i, Math.Min(nSize, bigList.Count - i));
			}
		}

		public static void UpdateState(string text)
		{
			MainWindow.FilesHave++;
			double num = double.Parse(MainWindow.FilesHave.ToString());
			double num1 = double.Parse(MainWindow.FilesNeed.ToString());
			double num2 = Math.Round(num / num1 * 579, 10);
			double num3 = Math.Round(num / num1 * 100);
			Application.Current.Dispatcher.Invoke(() => {
				MainWindow.WPF.checkClientInfo.Text = string.Concat(num3.ToString(), "%");
				MainWindow.WPF.progressBarFull.Width = num2;
			});
		}
	}
}
