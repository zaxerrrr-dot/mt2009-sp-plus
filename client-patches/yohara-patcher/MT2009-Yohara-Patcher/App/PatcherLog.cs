using System;
using System.IO;
using System.Text;

namespace MT2009Yohara
{
	// MT2009-Yohara-Patcher.log next to the game (the 2.x patcher writes
	// MT2009-Patcher-*.log): what the last runs did. Kept under ~512 KB.
	internal static class PatcherLog
	{
		public const string FileName = "MT2009-Yohara-Patcher.log";

		private static readonly object gate = new object();

		public static string Folder;

		public static bool Echo;

		public static void Write(string text)
		{
			string line = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  " + text;
			if (Echo)
			{
				try
				{
					Console.WriteLine(line);
				}
				catch
				{
				}
			}
			if (string.IsNullOrEmpty(Folder))
			{
				return;
			}
			lock (gate)
			{
				try
				{
					string path = Path.Combine(Folder, FileName);
					if (File.Exists(path) && new FileInfo(path).Length > 512 * 1024)
					{
						string old = path + ".1";
						if (File.Exists(old))
						{
							File.Delete(old);
						}
						File.Move(path, old);
					}
					File.AppendAllText(path, line + "\r\n", new UTF8Encoding(false));
				}
				catch
				{
				}
			}
		}
	}
}
