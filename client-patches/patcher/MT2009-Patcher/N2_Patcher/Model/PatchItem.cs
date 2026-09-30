using Newtonsoft.Json;
using System;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	public class PatchItem
	{
		[JsonProperty("delete")]
		public byte Delete
		{
			get;
			set;
		}

		[JsonProperty("name")]
		public string Filename
		{
			get;
			set;
		}

		[JsonProperty("size")]
		public long Filesize
		{
			get;
			set;
		}

		[JsonProperty("md5")]
		public string Md5Hash
		{
			get;
			set;
		}

		[JsonProperty("uid")]
		public string Uid
		{
			get;
			set;
		}

		public PatchItem()
		{
		}
	}
}