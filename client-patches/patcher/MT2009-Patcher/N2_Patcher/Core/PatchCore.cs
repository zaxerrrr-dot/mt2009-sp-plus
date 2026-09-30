using N2_Patcher.Model;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;

namespace N2_Patcher.Core
{
	// MT2009 PLUS: the patch list logic of the original (Functions.GetPatchlist,
	// GetMD5, GetFolder, the download address) without any WPF code, so the
	// same code runs in the patcher and in the Linux tests (MT2009-Patcher.Tests).
	//
	// Patch list = JSON array of PatchItem:
	//   {"name": "pack\\root.data", "size": 4124928, "md5": "<32 hex, UPPER>",
	//    "uid": "<path under Clientdata>", "delete": 0}
	// - name: path relative to the client folder, Windows separators (\).
	// - size: bytes; an entry with size 0 is ignored completely (also for delete).
	// - md5: compared as text with the upper-case MD5 of the local file.
	// - uid: the file is downloaded from Clientdata + uid.
	// - delete: > 0 = delete the local file if it exists (never downloaded).
	public static class PatchCore
	{
		public static List<PatchItem> ParsePatchlist(string json)
		{
			List<PatchItem> items = JsonConvert.DeserializeObject<List<PatchItem>>(json);
			return items ?? new List<PatchItem>();
		}

		// The names come from the server: never outside the client folder.
		public static bool IsSafeName(string name)
		{
			if (string.IsNullOrEmpty(name))
			{
				return false;
			}
			if (name.IndexOf(':') >= 0 || name.StartsWith("\\") || name.StartsWith("/"))
			{
				return false;
			}
			foreach (string part in name.Split(new char[] { '\\', '/' }))
			{
				if (part == ".." || part == "." || part.Length == 0)
				{
					return false;
				}
			}
			return true;
		}

		// folder ends with a separator (Functions.GetCurrentFolder() adds "\").
		// On Windows the name is used as is; elsewhere (tests) "\" becomes "/".
		public static string LocalPath(string folder, string name)
		{
			if (Path.DirectorySeparatorChar != '\\')
			{
				name = name.Replace('\\', Path.DirectorySeparatorChar);
			}
			return string.Concat(folder, name);
		}

		public static Uri DownloadUri(string clientdata, PatchItem item)
		{
			return new Uri(string.Concat(clientdata, item.Uid));
		}

		public static string GetMD5(string fileName)
		{
			using (FileStream fileStream = File.OpenRead(fileName))
			{
				using (MD5 mD5 = MD5.Create())
				{
					return BitConverter.ToString(mD5.ComputeHash(fileStream)).Replace("-", string.Empty);
				}
			}
		}

		public static string GetFolder(string Line)
		{
			char sep = Line.IndexOf('\\') >= 0 ? '\\' : Path.DirectorySeparatorChar;
			string str1 = "";
			string[] parts = Line.Split(new char[] { sep });
			for (int num = 0; num <= parts.Length - 2; num++)
			{
				str1 = string.Concat(str1, parts[num], sep.ToString());
			}
			return str1.Remove(str1.Length - 1);
		}

		// The files that must be downloaded; deletes the entries marked
		// "delete" on the way. The same rules as the original
		// Functions.GetPatchlist; onChecked runs once per entry (progress bar).
		public static List<PatchItem> SelectForDownload(List<PatchItem> patchlist, string folder, Action onChecked)
		{
			List<PatchItem> result = new List<PatchItem>();
			foreach (PatchItem patchItem in patchlist)
			{
				if (patchItem.Filesize != 0 && PatchCore.IsSafeName(patchItem.Filename))
				{
					string path = PatchCore.LocalPath(folder, patchItem.Filename);
					if (!File.Exists(path))
					{
						if (patchItem.Delete == 0)
						{
							result.Add(patchItem);
						}
					}
					else if (patchItem.Delete > 0)
					{
						File.Delete(path);
					}
					else if (!string.Equals(PatchCore.GetMD5(path), patchItem.Md5Hash, StringComparison.Ordinal))
					{
						result.Add(patchItem);
					}
				}
				onChecked?.Invoke();
			}
			return result;
		}
	}
}
