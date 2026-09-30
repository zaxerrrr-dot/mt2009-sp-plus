using Newtonsoft.Json;
using System;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	public class SliderItem
	{
		[JsonProperty("Content")]
		public string content
		{
			get;
			set;
		}

		[JsonProperty("Content-Type")]
		public short contentType
		{
			get;
			set;
		}

		[JsonProperty("Duration")]
		public int duration
		{
			get;
			set;
		}

		[JsonProperty("Image-Type")]
		public string imgType
		{
			get;
			set;
		}

		[JsonProperty("Image-Url")]
		public string imgUrl
		{
			get;
			set;
		}

		[JsonProperty("Link-Url")]
		public string linkUrl
		{
			get;
			set;
		}

		[JsonProperty("Position")]
		public short position
		{
			get;
			set;
		}

		[JsonProperty("Title")]
		public string title
		{
			get;
			set;
		}

		public SliderItem()
		{
		}
	}
}