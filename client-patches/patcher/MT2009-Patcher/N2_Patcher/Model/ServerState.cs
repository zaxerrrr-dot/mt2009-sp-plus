using Newtonsoft.Json;
using System;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	public class ServerState
	{
		[JsonProperty("Accounts")]
		public long Accounts
		{
			get;
			set;
		}

		[JsonProperty("Channel")]
		public ChannelState Channel
		{
			get;
			set;
		}

		[JsonProperty("Charaktere")]
		public long Charaktere
		{
			get;
			set;
		}

		[JsonProperty("Online")]
		public long Online
		{
			get;
			set;
		}

		public ServerState()
		{
		}
	}
}