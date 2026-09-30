using System;
using System.CodeDom.Compiler;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Windows;

namespace N2_Patcher
{
	public partial class App : Application
	{
		// MT2009 PLUS: Newtonsoft.Json.dll is embedded in the exe, so players
		// need only MT2009-Patcher.exe (+ optional .config).
		static App()
		{
			AppDomain.CurrentDomain.AssemblyResolve += App.ResolveEmbedded;
		}

		public App()
		{
		}

		private static readonly object resolveLock = new object();

		private static readonly System.Collections.Generic.Dictionary<string, Assembly> resolved = new System.Collections.Generic.Dictionary<string, Assembly>();

		// Loaded once and cached: the news and patch list threads ask for it at
		// the same time, and two copies of one assembly break its types.
		private static Assembly ResolveEmbedded(object sender, ResolveEventArgs args)
		{
			string name = new AssemblyName(args.Name).Name + ".dll";
			lock (App.resolveLock)
			{
				Assembly cached;
				if (App.resolved.TryGetValue(name, out cached))
				{
					return cached;
				}
				Assembly loaded = App.LoadEmbedded(name);
				if (loaded != null)
				{
					App.resolved[name] = loaded;
				}
				return loaded;
			}
		}

		private static Assembly LoadEmbedded(string name)
		{
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
				return Assembly.Load(data);
			}
		}

		protected override void OnStartup(StartupEventArgs e)
		{
			string exe = Assembly.GetEntryAssembly().Location;
			// The patcher works on the folder it lies in (a shortcut may start
			// it with another working folder).
			try
			{
				Directory.SetCurrentDirectory(Path.GetDirectoryName(exe));
			}
			catch
			{
			}
			// After a self-update: wait until the old patcher has ended.
			if (e.Args.Length >= 2 && e.Args[0] == Program.AfterUpdateArgument)
			{
				int pid;
				if (int.TryParse(e.Args[1], out pid))
				{
					try
					{
						Process.GetProcessById(pid).WaitForExit(15000);
					}
					catch
					{
					}
				}
			}
			if (Process.GetProcessesByName(Path.GetFileNameWithoutExtension(exe)).Count<Process>() > 1)
			{
				Environment.Exit(0);
			}
			base.OnStartup(e);
		}
	}
}
