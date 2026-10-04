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

		// MT2009 PLUS: 1 = the player's own copy wins - downloaded only when
		// missing, never "repaired" (pack\dbdata.*, the database editor's
		// files the player unpacks from the server's panel). Older patchers
		// ignore the field.
		[JsonProperty("keep")]
		public byte Keep
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
