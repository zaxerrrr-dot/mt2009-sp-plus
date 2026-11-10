using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;

namespace MT2009Yohara.Core
{
	// The network side of Updater (replaceable in tests).
	public interface IHttp
	{
		string GetString(string url);

		// Writes url to "path": from byte "offset" on (appended, HTTP Range)
		// or, with offset 0 / a server that ignores the range, the whole file
		// (path truncated). Returns the offset really used (0 = whole file).
		long Download(string url, string path, long offset, Action<long> onBytes, CancellationToken cancel);
	}

	public class HttpError : Exception
	{
		public int Status { get; private set; }

		public HttpError(int status, string message) : base(message)
		{
			this.Status = status;
		}
	}

	public class WebHttp : IHttp
	{
		public const string UserAgent = "MT2009-Yohara-Patcher/1 (.NET)";

		public int TimeoutMs = 30000;

		static WebHttp()
		{
			try
			{
				ServicePointManager.SecurityProtocol |= SecurityProtocolType.Tls12;
				ServicePointManager.Expect100Continue = false;
				ServicePointManager.DefaultConnectionLimit = Math.Max(ServicePointManager.DefaultConnectionLimit, 4);
			}
			catch
			{
			}
		}

		private HttpWebRequest Create(string url)
		{
			HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
			request.UserAgent = UserAgent;
			request.Proxy = null;
			request.Timeout = this.TimeoutMs;
			request.ReadWriteTimeout = this.TimeoutMs;
			request.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;
			request.CachePolicy = new System.Net.Cache.RequestCachePolicy(System.Net.Cache.RequestCacheLevel.NoCacheNoStore);
			return request;
		}

		private static HttpWebResponse Send(HttpWebRequest request)
		{
			try
			{
				return (HttpWebResponse)request.GetResponse();
			}
			catch (WebException e) when (e.Response is HttpWebResponse)
			{
				HttpWebResponse r = (HttpWebResponse)e.Response;
				int status = (int)r.StatusCode;
				r.Close();
				throw new HttpError(status, string.Format("HTTP {0} - {1}", status, request.RequestUri));
			}
		}

		public string GetString(string url)
		{
			HttpWebRequest request = this.Create(url);
			using (HttpWebResponse response = Send(request))
			using (Stream stream = response.GetResponseStream())
			using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
			{
				return reader.ReadToEnd();
			}
		}

		public long Download(string url, string path, long offset, Action<long> onBytes, CancellationToken cancel)
		{
			HttpWebRequest request = this.Create(url);
			// the store files are already compressed packs: no gzip on the way
			request.AutomaticDecompression = DecompressionMethods.None;
			if (offset > 0)
			{
				request.AddRange(offset);
			}
			HttpWebResponse response;
			try
			{
				response = Send(request);
			}
			catch (HttpError e) when (e.Status == 416 && offset > 0)
			{
				// the part is already whole (or longer): the caller checks it
				return offset;
			}
			using (response)
			{
				bool ranged = offset > 0 && response.StatusCode == HttpStatusCode.PartialContent;
				if (offset > 0 && !ranged)
				{
					// the server sent the whole file: start the part over
					offset = 0;
				}
				using (Stream body = response.GetResponseStream())
				using (FileStream file = new FileStream(path, offset > 0 ? FileMode.Append : FileMode.Create, FileAccess.Write, FileShare.None, 1 << 16))
				{
					byte[] buffer = new byte[1 << 16];
					int n;
					while ((n = body.Read(buffer, 0, buffer.Length)) > 0)
					{
						cancel.ThrowIfCancellationRequested();
						file.Write(buffer, 0, n);
						onBytes?.Invoke(n);
					}
				}
				return offset;
			}
		}
	}
}
