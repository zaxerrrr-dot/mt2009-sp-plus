using N2_Patcher.Model;
using System;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading.Tasks;

namespace N2_Patcher.Core
{
	// MT2009 PLUS: server status without a web endpoint. The original read a
	// JSON from the "Stats" address (ServerState: Accounts, Charaktere,
	// Online, Channel = {Auth, CH1..CH4, CH99}); an MT2009 server has no
	// such page, so the patcher opens a TCP connection to the login port and
	// to each channel port of the chosen server (coop.cfg / coop2.cfg /
	// localhost) and fills the same ChannelState.
	public static class ServerProbe
	{
		public static async Task<bool> IsOpen(string host, int port, int timeoutMs)
		{
			using (TcpClient client = new TcpClient())
			{
				try
				{
					Task connect = client.ConnectAsync(host, port);
					Task done = await Task.WhenAny(connect, Task.Delay(timeoutMs)).ConfigureAwait(false);
					if (done != connect)
					{
						// Observe the late result so it is not an unobserved exception.
						_ = connect.ContinueWith(t => { var _ignored = t.Exception; }, TaskContinuationOptions.OnlyOnFaulted);
						return false;
					}
					await connect.ConfigureAwait(false);
					return client.Connected;
				}
				catch
				{
					return false;
				}
			}
		}

		public static async Task<ChannelState> Probe(CoopServer server, int timeoutMs = 2000)
		{
			int[] ports = server.ChannelPorts;
			List<Task<bool>> tasks = new List<Task<bool>> { IsOpen(server.Host, server.Auth, timeoutMs) };
			foreach (int port in ports)
			{
				tasks.Add(IsOpen(server.Host, port, timeoutMs));
			}
			bool[] open = await Task.WhenAll(tasks).ConfigureAwait(false);
			return new ChannelState
			{
				auth = open[0],
				channel_1 = open.Length > 1 && open[1],
				channel_2 = open.Length > 2 && open[2]
			};
		}
	}
}
