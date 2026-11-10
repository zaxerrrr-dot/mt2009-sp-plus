using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;

namespace MT2009Yohara
{
	// Newtonsoft.Json.dll is embedded in the exe: the player gets one file.
	// Loaded once and cached (two copies of one assembly break its types).
	// No WPF here, so "--cli" works without loading the window code.
	internal static class Embedded
	{
		private static readonly object gate = new object();

		private static readonly Dictionary<string, Assembly> loaded = new Dictionary<string, Assembly>();

		private static bool installed;

		public static void Install()
		{
			lock (gate)
			{
				if (!installed)
				{
					installed = true;
					AppDomain.CurrentDomain.AssemblyResolve += Resolve;
				}
			}
		}

		private static Assembly Resolve(object sender, ResolveEventArgs args)
		{
			string name = new AssemblyName(args.Name).Name + ".dll";
			lock (gate)
			{
				Assembly cached;
				if (loaded.TryGetValue(name, out cached))
				{
					return cached;
				}
				using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(name))
				{
					if (stream == null)
					{
						return null;
					}
					byte[] data = new byte[stream.Length];
					int read = 0;
					while (read < data.Length)
					{
						int n = stream.Read(data, read, data.Length - read);
						if (n <= 0)
						{
							break;
						}
						read += n;
					}
					Assembly assembly = Assembly.Load(data);
					loaded[name] = assembly;
					return assembly;
				}
			}
		}
	}
}
