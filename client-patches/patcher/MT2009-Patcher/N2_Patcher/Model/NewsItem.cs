using Newtonsoft.Json;
using System;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	public class NewsItem
	{
		[JsonProperty("avatarLink")]
		public string avatarLink
		{
			get;
			set;
		}

		[JsonProperty("creator")]
		public string creator
		{
			get;
			set;
		}

		[JsonProperty("date")]
		public string date
		{
			get;
			set;
		}

		[JsonProperty("message")]
		public string message
		{
			get;
			set;
		}

		[JsonProperty("newsType")]
		public int newsType
		{
			get;
			set;
		}

		[JsonProperty("threadUrl")]
		public string threadUrl
		{
			get;
			set;
		}

		[JsonProperty("topic")]
		public string topic
		{
			get;
			set;
		}

		public NewsItem()
		{
		}
	}
}