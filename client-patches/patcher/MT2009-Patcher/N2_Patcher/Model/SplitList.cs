using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;

namespace N2_Patcher.Model
{
	internal class SplitList
	{
		public List<PatchItem> List1
		{
			get;
			set;
		}

		public List<PatchItem> List2
		{
			get;
			set;
		}

		public List<PatchItem> List3
		{
			get;
			set;
		}

		public List<PatchItem> List4
		{
			get;
			set;
		}

		public List<PatchItem> List5
		{
			get;
			set;
		}

		public List<PatchItem> List6
		{
			get;
			set;
		}

		public List<PatchItem> List7
		{
			get;
			set;
		}

		public List<PatchItem> List8
		{
			get;
			set;
		}

		public SplitList(List<PatchItem> patchlist)
		{
			this.List1 = new List<PatchItem>();
			this.List2 = new List<PatchItem>();
			this.List3 = new List<PatchItem>();
			this.List4 = new List<PatchItem>();
			this.List5 = new List<PatchItem>();
			this.List6 = new List<PatchItem>();
			this.List7 = new List<PatchItem>();
			this.List8 = new List<PatchItem>();
			for (int i = 0; i < patchlist.Count; i++)
			{
				if (i % 8 > 0)
				{
					this.List8.Add(patchlist[i]);
				}
				else if (i % 7 > 0)
				{
					this.List7.Add(patchlist[i]);
				}
				else if (i % 6 > 0)
				{
					this.List6.Add(patchlist[i]);
				}
				else if (i % 5 > 0)
				{
					this.List5.Add(patchlist[i]);
				}
				else if (i % 4 > 0)
				{
					this.List4.Add(patchlist[i]);
				}
				else if (i % 3 > 0)
				{
					this.List3.Add(patchlist[i]);
				}
				else if (i % 2 <= 0)
				{
					this.List1.Add(patchlist[i]);
				}
				else
				{
					this.List2.Add(patchlist[i]);
				}
			}
		}
	}
}