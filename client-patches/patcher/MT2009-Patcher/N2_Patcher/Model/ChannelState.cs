using Newtonsoft.Json;
using System;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	public class ChannelState
	{
		[JsonProperty("Auth")]
		public bool auth
		{
			get;
			set;
		}

		[JsonProperty("CH1")]
		public bool channel_1
		{
			get;
			set;
		}

		[JsonProperty("CH2")]
		public bool channel_2
		{
			get;
			set;
		}

		[JsonProperty("CH3")]
		public bool channel_3
		{
			get;
			set;
		}

		[JsonProperty("CH4")]
		public bool channel_4
		{
			get;
			set;
		}

		[JsonProperty("CH99")]
		public bool channel_99
		{
			get;
			set;
		}

		public ChannelState()
		{
		}
	}
}