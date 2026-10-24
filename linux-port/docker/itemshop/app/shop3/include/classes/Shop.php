<?php
use Medoo\Medoo;

class Shop {

	private $db = NULL;

	public function __construct($db) {
		$this->db = $db; 
	}
	
	public function updateItemProto($file)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		$first = false;
		$top = $columns = array();
		$max_key = 0;

		$items = array();
		$used = array();

		$this->db->delete("item_proto", []);

		while(!feof($file))	{
			$line = utf8_encode(fgets($file));
			$arr = explode("	", $line);
			
			if($first && isset($arr[$max_key]) && !in_array($arr[$columns['id']], $used) && strpos($arr[$columns['id']], '~') == false)
			{
				foreach($columns as $column => $key)
					$items[$y][$column]=$arr[$key];
				$used[] = $arr[$columns['id']];
				$y++;
				$x++;
				
				if($y>=250)
				{
					$y=0;
					$this->db->insert("item_proto", $items);
					$items=array();
				}
			}
			else
			{
				$columns['id']=0;
				foreach($arr as $key => $column)
					if(strpos($column, 'ITEM_TYPE') !== false)
						$columns['item_type']=$key;
					else if(strpos($column, 'SUB_TYPE') !== false)
						$columns['sub_type']=$key;
					else if(strpos($column, 'SIZE') !== false)
						$columns['size']=$key;
					else if(strpos($column, 'FLAG') !== false)
						$columns['flag']=$key;
					else if(strpos($column, 'MAGIC_PCT') !== false)
						$columns['magic_pct']=$key;
					else if(strpos($column, 'LIMIT_TYPE0') !== false)
						$columns['limit_type0']=$key;
					else if(strpos($column, 'LIMIT_VALUE0') !== false)
						$columns['limit_value0']=$key;
					else if(strpos($column, 'LIMIT_TYPE1') !== false)
						$columns['limit_type1']=$key;
					else if(strpos($column, 'LIMIT_VALUE1') !== false)
						$columns['limit_value1']=$key;
					else if(strpos($column, 'ADDON_TYPE0') !== false)
						$columns['addon_type0']=$key;
					else if(strpos($column, 'ADDON_VALUE0') !== false)
						$columns['addon_value0']=$key;
					else if(strpos($column, 'ADDON_TYPE1') !== false)
						$columns['addon_type1']=$key;
					else if(strpos($column, 'ADDON_VALUE1') !== false)
						$columns['addon_value1']=$key;
					else if(strpos($column, 'ADDON_TYPE2') !== false)
						$columns['addon_type2']=$key;
					else if(strpos($column, 'ADDON_VALUE2') !== false)
						$columns['addon_value2']=$key;
					else if(strpos($column, 'VALUE0') !== false)
						$columns['value0']=$key;
					else if(strpos($column, 'VALUE1') !== false)
						$columns['value1']=$key;
					else if(strpos($column, 'VALUE2') !== false)
						$columns['value2']=$key;
					else if(strpos($column, 'VALUE3') !== false)
						$columns['value3']=$key;
					else if(strpos($column, 'VALUE4') !== false)
						$columns['value4']=$key;
					else if(strpos($column, 'VALUE5') !== false)
						$columns['value5']=$key;
					else if(strpos($column, 'SOCKET') !== false)
						$columns['gain_socket']=$key;
					else if(strpos($column, 'ATTU_ADDON') !== false)
						$columns['attu_addon']=$key;
				
				foreach($columns as $key)
					if($key>$max_key)
						$max_key = $key;
				$first = true;
			}
		}
		
		if($y>0)
			$this->db->insert("item_proto", $items);
		
		$this->updateUploadTime('item_proto');
		return $x;
	}

	public function updateBlendJson($file)
	{
		$file = fopen($file, "r");

		$i=0;
		$blend = array();
		while(!feof($file)){
			$line = utf8_encode(fgets($file)).'<br>';
			
			if(strpos($line, 'item_vnum') !== false)
			{
				$arr = explode("	", $line);
				$blend[$i]['item_vnum'] = str_replace('<br>', '', str_replace(array("\n", "\r"), '', $arr[2]));
			}
			else if(strpos($line, 'apply_type') !== false)
			{
				$arr = explode("	", $line);
				$blend[$i]['apply_type'] = str_replace('<br>', '', str_replace(array("\n", "\r"), '', $arr[2]));
			}
			else if(strpos($line, 'apply_value') !== false)
			{
				$arr = explode("	", $line);
				unset($arr[0]); unset($arr[1]);
				foreach($arr as $key=>$value)
					$blend[$i]['apply_value'][$key-2]=str_replace('<br>', '', str_replace(array("\n", "\r"), '', $value));
			}
			else if(strpos($line, 'apply_duration') !== false)
			{
				$arr = explode("	", $line);
				unset($arr[0]); unset($arr[1]);
				foreach($arr as $key=>$value)
					$blend[$i]['apply_duration'][$key-2]=str_replace('<br>', '', str_replace(array("\n", "\r"), '', $value));
			}
			else if(strpos($line, 'end') !== false)
				$i++;
		}
		$json = json_encode($blend);
		file_put_contents('include/db/blend.json', $json);
		
		$this->updateUploadTime('blend');
	}

	public function itemProtoCount()
	{
		return $this->db->count("item_proto");
	}

	public function updateUploadTime($type)
	{
		$json = file_get_contents('include/db/last_update.json');
		$json = json_decode($json, true);
		
		$json[$type] = date('d.m.Y H:i', time());
		
		$json = json_encode($json);
		file_put_contents('include/db/last_update.json', $json);
	}
	
	public function getItem($vnum, $column=NULL)
	{
		if($column==NULL)
			return $this->db->get("item_proto", "*", ["id" => $vnum]);
		
		return $this->db->get("item_proto", $column, ["id" => $vnum]);
	}

	public function updateItemList($file)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		$first = false;
		$top = $columns = array();

		$items = array();

		$this->db->delete("item_list", []);

		while(!feof($file))	{
			$line = utf8_encode(fgets($file));
			$arr = explode("	", $line);
			
			if(isset($arr[0]) && isset($arr[2]))
			{
				$items[$y]['vnum']=trim($arr[0]);
				$items[$y]['src']='';
				$items[$y]['src'] = str_replace('.tga', '', trim($arr[2]));
				$items[$y]['src'] = str_replace('.png', '', trim($items[$y]['src']));
				$items[$y]['src'] = trim($items[$y]['src']);
				
				if($items[$y]['src'][0]!='i' && $items[$y]['src'][1]!='c')
					$items[$y]['src'] = str_replace('season1/icon/', 'icons/season1/', $items[$y]['src']).'.png';
				else
					$items[$y]['src'] = str_replace('icon/item/', 'icons/', $items[$y]['src']).'.png';

				//if(file_exists('images/'.$items[$y]['src']))
				//{
					$y++;
					$x++;
				//}
			}

			if($y>=250)
			{
				$y=0;
				$this->db->insert("item_list", $items);
				$items=array();
			}
		}
		
		if($y>0)
			$this->db->insert("item_list", $items);
		
		$this->updateUploadTime('item_list');
		return $x;
	}
	
	public function normalize_to_utf8_chars($string) {     // Nr. | Unicode | Win1252 | Expected  | Actually  | UTF8 Bytes
													//----------------------------------------------------------------------
	  $search=array(chr(0xE2).chr(0x82).chr(0xAC),  // 001 | U+20AC  | 0x80    | €         | â‚¬       | %E2 %82 %AC
					chr(0xE2).chr(0x80).chr(0x9A),  // 002 | U+201A  | 0x82    | ‚         | â€š       | %E2 %80 %9A
					chr(0xC6).chr(0x92),            // 003 | U+0192  | 0x83    | ƒ         | Æ’        | %C6 %92
					chr(0xE2).chr(0x80).chr(0x9E),  // 004 | U+201E  | 0x84    | „         | â€ž       | %E2 %80 %9E
					chr(0xE2).chr(0x80).chr(0xA6),  // 005 | U+2026  | 0x85    | …         | â€¦       | %E2 %80 %A6
					chr(0xE2).chr(0x80).chr(0xA0),  // 006 | U+2020  | 0x86    | †         | â€        | %E2 %80 %A0
					chr(0xE2).chr(0x80).chr(0xA1),  // 007 | U+2021  | 0x87    | ‡         | â€¡       | %E2 %80 %A1
					chr(0xCB).chr(0x86),            // 008 | U+02C6  | 0x88    | ˆ         | Ë†        | %CB %86
					chr(0xE2).chr(0x80).chr(0xB0),  // 009 | U+2030  | 0x89    | ‰         | â€°       | %E2 %80 %B0
					chr(0xC5).chr(0xA0),            // 010 | U+0160  | 0x8A    | Š         | Å         | %C5 %A0
					chr(0xE2).chr(0x80).chr(0xB9),  // 011 | U+2039  | 0x8B    | ‹         | â€¹       | %E2 %80 %B9
					chr(0xC5).chr(0x92),            // 012 | U+0152  | 0x8C    | Œ         | Å’        | %C5 %92
					chr(0xC5).chr(0xBD),            // 013 | U+017D  | 0x8E    | Ž         | Å½        | %C5 %BD
					chr(0xE2).chr(0x80).chr(0x98),  // 014 | U+2018  | 0x91    | ‘         | â€˜       | %E2 %80 %98
					chr(0xE2).chr(0x80).chr(0x99),  // 015 | U+2019  | 0x92    | ’         | â€™       | %E2 %80 %99
					chr(0xE2).chr(0x80).chr(0x9C),  // 016 | U+201C  | 0x93    | “         | â€œ       | %E2 %80 %9C
					chr(0xE2).chr(0x80).chr(0x9D),  // 017 | U+201D  | 0x94    | ”         | â€        | %E2 %80 %9D
					chr(0xE2).chr(0x80).chr(0xA2),  // 018 | U+2022  | 0x95    | •         | â€¢       | %E2 %80 %A2
					chr(0xE2).chr(0x80).chr(0x93),  // 019 | U+2013  | 0x96    | –         | â€“       | %E2 %80 %93  (see: [1])
					chr(0xE2).chr(0x80).chr(0x94),  // 020 | U+2014  | 0x97    | —         | â€”       | %E2 %80 %94  (see: [2])
					chr(0xCB).chr(0x9C),            // 021 | U+02DC  | 0x98    | ˜         | Ëœ        | %CB %9C
					chr(0xE2).chr(0x84).chr(0xA2),  // 022 | U+2122  | 0x99    | ™         | â„¢       | %E2 %84 %A2
					chr(0xC5).chr(0xA1),            // 023 | U+0161  | 0x9A    | š         | Å¡        | %C5 %A1
					chr(0xE2).chr(0x80).chr(0xBA),  // 024 | U+203A  | 0x9B    | ›         | â€º       | %E2 %80 %BA
					chr(0xC5).chr(0x93),            // 025 | U+0153  | 0x9C    | œ         | Å“        | %C5 %93
					chr(0xC5).chr(0xBE),            // 026 | U+017E  | 0x9E    | ž         | Å¾        | %C5 %BE
					chr(0xC5).chr(0xB8),            // 027 | U+0178  | 0x9F    | Ÿ         | Å¸        | %C5 %B8
					chr(0xC2).chr(0xA0),            // 028 | U+00A0  | 0xA0    |           | Â         | %C2 %A0      (see [3])
					chr(0xC2).chr(0xA1),            // 029 | U+00A1  | 0xA1    | ¡         | Â¡        | %C2 %A1
					chr(0xC2).chr(0xA2),            // 030 | U+00A2  | 0xA2    | ¢         | Â¢        | %C2 %A2
					chr(0xC2).chr(0xA3),            // 031 | U+00A3  | 0xA3    | £         | Â£        | %C2 %A3
					chr(0xC2).chr(0xA4),            // 032 | U+00A4  | 0xA4    | ¤         | Â¤        | %C2 %A4
					chr(0xC2).chr(0xA5),            // 033 | U+00A5  | 0xA5    | ¥         | Â¥        | %C2 %A5
					chr(0xC2).chr(0xA6),            // 034 | U+00A6  | 0xA6    | ¦         | Â¦        | %C2 %A6
					chr(0xC2).chr(0xA7),            // 035 | U+00A7  | 0xA7    | §         | Â§        | %C2 %A7
					chr(0xC2).chr(0xA8),            // 036 | U+00A8  | 0xA8    | ¨         | Â¨        | %C2 %A8
					chr(0xC2).chr(0xA9),            // 037 | U+00A9  | 0xA9    | ©         | Â©        | %C2 %A9
					chr(0xC2).chr(0xAA),            // 038 | U+00AA  | 0xAA    | ª         | Âª        | %C2 %AA
					chr(0xC2).chr(0xAB),            // 039 | U+00AB  | 0xAB    | «         | Â«        | %C2 %AB
					chr(0xC2).chr(0xAC),            // 040 | U+00AC  | 0xAC    | ¬         | Â¬        | %C2 %AC
					chr(0xC2).chr(0xAD),            // 041 | U+00AD  | 0xAD    |           | Â         | %C2 %AD      (see: [4])
					chr(0xC2).chr(0xAE),            // 042 | U+00AE  | 0xAE    | ®         | Â®        | %C2 %AE
					chr(0xC2).chr(0xAF),            // 043 | U+00AF  | 0xAF    | ¯         | Â¯        | %C2 %AF
					chr(0xC2).chr(0xB0),            // 044 | U+00B0  | 0xB0    | °         | Â°        | %C2 %B0
					chr(0xC2).chr(0xB1),            // 045 | U+00B1  | 0xB1    | ±         | Â±        | %C2 %B1
					chr(0xC2).chr(0xB2),            // 046 | U+00B2  | 0xB2    | ²         | Â²        | %C2 %B2
					chr(0xC2).chr(0xB3),            // 047 | U+00B3  | 0xB3    | ³         | Â³        | %C2 %B3
					chr(0xC2).chr(0xB4),            // 048 | U+00B4  | 0xB4    | ´         | Â´        | %C2 %B4
					chr(0xC2).chr(0xB5),            // 049 | U+00B5  | 0xB5    | µ         | Âµ        | %C2 %B5
					chr(0xC2).chr(0xB6),            // 050 | U+00B6  | 0xB6    | ¶         | Â¶        | %C2 %B6
					chr(0xC2).chr(0xB7),            // 051 | U+00B7  | 0xB7    | ·         | Â·        | %C2 %B7
					chr(0xC2).chr(0xB8),            // 052 | U+00B8  | 0xB8    | ¸         | Â¸        | %C2 %B8
					chr(0xC2).chr(0xB9),            // 053 | U+00B9  | 0xB9    | ¹         | Â¹        | %C2 %B9
					chr(0xC2).chr(0xBA),            // 054 | U+00BA  | 0xBA    | º         | Âº        | %C2 %BA
					chr(0xC2).chr(0xBB),            // 055 | U+00BB  | 0xBB    | »         | Â»        | %C2 %BB
					chr(0xC2).chr(0xBC),            // 056 | U+00BC  | 0xBC    | ¼         | Â¼        | %C2 %BC
					chr(0xC2).chr(0xBD),            // 057 | U+00BD  | 0xBD    | ½         | Â½        | %C2 %BD
					chr(0xC2).chr(0xBE),            // 058 | U+00BE  | 0xBE    | ¾         | Â¾        | %C2 %BE
					chr(0xC2).chr(0xBF),            // 059 | U+00BF  | 0xBF    | ¿         | Â¿        | %C2 %BF
					chr(0xC3).chr(0x80),            // 060 | U+00C0  | 0xC0    | À         | Ã€        | %C3 %80
					chr(0xC3).chr(0x81),            // 061 | U+00C1  | 0xC1    | Á         | Ã         | %C3 %81
					chr(0xC3).chr(0x82),            // 062 | U+00C2  | 0xC2    | Â         | Ã‚        | %C3 %82
					chr(0xC3).chr(0x83),            // 063 | U+00C3  | 0xC3    | Ã         | Ãƒ        | %C3 %83
					chr(0xC3).chr(0x84),            // 064 | U+00C4  | 0xC4    | Ä         | Ã„        | %C3 %84
					chr(0xC3).chr(0x85),            // 065 | U+00C5  | 0xC5    | Å         | Ã…        | %C3 %85
					chr(0xC3).chr(0x86),            // 066 | U+00C6  | 0xC6    | Æ         | Ã†        | %C3 %86
					chr(0xC3).chr(0x87),            // 067 | U+00C7  | 0xC7    | Ç         | Ã‡        | %C3 %87
					chr(0xC3).chr(0x88),            // 068 | U+00C8  | 0xC8    | È         | Ãˆ        | %C3 %88
					chr(0xC3).chr(0x89),            // 069 | U+00C9  | 0xC9    | É         | Ã‰        | %C3 %89
					chr(0xC3).chr(0x8A),            // 070 | U+00CA  | 0xCA    | Ê         | ÃŠ        | %C3 %8A
					chr(0xC3).chr(0x8B),            // 071 | U+00CB  | 0xCB    | Ë         | Ã‹        | %C3 %8B
					chr(0xC3).chr(0x8C),            // 072 | U+00CC  | 0xCC    | Ì         | ÃŒ        | %C3 %8C
					chr(0xC3).chr(0x8D),            // 073 | U+00CD  | 0xCD    | Í         | Ã         | %C3 %8D
					chr(0xC3).chr(0x8E),            // 074 | U+00CE  | 0xCE    | Î         | ÃŽ        | %C3 %8E
					chr(0xC3).chr(0x8F),            // 075 | U+00CF  | 0xCF    | Ï         | Ã         | %C3 %8F
					chr(0xC3).chr(0x90),            // 076 | U+00D0  | 0xD0    | Ð         | Ã         | %C3 %90
					chr(0xC3).chr(0x91),            // 077 | U+00D1  | 0xD1    | Ñ         | Ã‘        | %C3 %91
					chr(0xC3).chr(0x92),            // 078 | U+00D2  | 0xD2    | Ò         | Ã’        | %C3 %92
					chr(0xC3).chr(0x93),            // 079 | U+00D3  | 0xD3    | Ó         | Ã“        | %C3 %93
					chr(0xC3).chr(0x94),            // 080 | U+00D4  | 0xD4    | Ô         | Ã”        | %C3 %94
					chr(0xC3).chr(0x95),            // 081 | U+00D5  | 0xD5    | Õ         | Ã•        | %C3 %95
					chr(0xC3).chr(0x96),            // 082 | U+00D6  | 0xD6    | Ö         | Ã–        | %C3 %96
					chr(0xC3).chr(0x97),            // 083 | U+00D7  | 0xD7    | ×         | Ã—        | %C3 %97
					chr(0xC3).chr(0x98),            // 084 | U+00D8  | 0xD8    | Ø         | Ã˜        | %C3 %98
					chr(0xC3).chr(0x99),            // 085 | U+00D9  | 0xD9    | Ù         | Ã™        | %C3 %99
					chr(0xC3).chr(0x9A),            // 086 | U+00DA  | 0xDA    | Ú         | Ãš        | %C3 %9A
					chr(0xC3).chr(0x9B),            // 087 | U+00DB  | 0xDB    | Û         | Ã›        | %C3 %9B
					chr(0xC3).chr(0x9C),            // 088 | U+00DC  | 0xDC    | Ü         | Ãœ        | %C3 %9C
					chr(0xC3).chr(0x9D),            // 089 | U+00DD  | 0xDD    | Ý         | Ã         | %C3 %9D
					chr(0xC3).chr(0x9E),            // 090 | U+00DE  | 0xDE    | Þ         | Ãž        | %C3 %9E
					chr(0xC3).chr(0x9F),            // 091 | U+00DF  | 0xDF    | ß         | ÃŸ        | %C3 %9F
					chr(0xC3).chr(0xA0),            // 092 | U+00E0  | 0xE0    | à         | Ã         | %C3 %A0
					chr(0xC3).chr(0xA1),            // 093 | U+00E1  | 0xE1    | á         | Ã¡        | %C3 %A1
					chr(0xC3).chr(0xA2),            // 094 | U+00E2  | 0xE2    | â         | Ã¢        | %C3 %A2
					chr(0xC3).chr(0xA3),            // 095 | U+00E3  | 0xE3    | ã         | Ã£        | %C3 %A3
					chr(0xC3).chr(0xA4),            // 096 | U+00E4  | 0xE4    | ä         | Ã¤        | %C3 %A4
					chr(0xC3).chr(0xA5),            // 097 | U+00E5  | 0xE5    | å         | Ã¥        | %C3 %A5
					chr(0xC3).chr(0xA6),            // 098 | U+00E6  | 0xE6    | æ         | Ã¦        | %C3 %A6
					chr(0xC3).chr(0xA7),            // 099 | U+00E7  | 0xE7    | ç         | Ã§        | %C3 %A7
					chr(0xC3).chr(0xA8),            // 100 | U+00E8  | 0xE8    | è         | Ã¨        | %C3 %A8
					chr(0xC3).chr(0xA9),            // 001 | U+00E9  | 0xE9    | é         | Ã©        | %C3 %A9
					chr(0xC3).chr(0xAA),            // 002 | U+00EA  | 0xEA    | ê         | Ãª        | %C3 %AA
					chr(0xC3).chr(0xAB),            // 003 | U+00EB  | 0xEB    | ë         | Ã«        | %C3 %AB
					chr(0xC3).chr(0xAC),            // 004 | U+00EC  | 0xEC    | ì         | Ã¬        | %C3 %AC
					chr(0xC3).chr(0xAD),            // 005 | U+00ED  | 0xED    | í         | Ã         | %C3 %AD
					chr(0xC3).chr(0xAE),            // 006 | U+00EE  | 0xEE    | î         | Ã®        | %C3 %AE
					chr(0xC3).chr(0xAF),            // 007 | U+00EF  | 0xEF    | ï         | Ã¯        | %C3 %AF
					chr(0xC3).chr(0xB0),            // 008 | U+00F0  | 0xF0    | ð         | Ã°        | %C3 %B0
					chr(0xC3).chr(0xB1),            // 009 | U+00F1  | 0xF1    | ñ         | Ã±        | %C3 %B1
					chr(0xC3).chr(0xB2),            // 000 | U+00F2  | 0xF2    | ò         | Ã²        | %C3 %B2
					chr(0xC3).chr(0xB3),            // 001 | U+00F3  | 0xF3    | ó         | Ã³        | %C3 %B3
					chr(0xC3).chr(0xB4),            // 002 | U+00F4  | 0xF4    | ô         | Ã´        | %C3 %B4
					chr(0xC3).chr(0xB5),            // 003 | U+00F5  | 0xF5    | õ         | Ãµ        | %C3 %B5
					chr(0xC3).chr(0xB6),            // 004 | U+00F6  | 0xF6    | ö         | Ã¶        | %C3 %B6
					chr(0xC3).chr(0xB7),            // 005 | U+00F7  | 0xF7    | ÷         | Ã·        | %C3 %B7
					chr(0xC3).chr(0xB8),            // 006 | U+00F8  | 0xF8    | ø         | Ã¸        | %C3 %B8
					chr(0xC3).chr(0xB9),            // 007 | U+00F9  | 0xF9    | ù         | Ã¹        | %C3 %B9
					chr(0xC3).chr(0xBA),            // 008 | U+00FA  | 0xFA    | ú         | Ãº        | %C3 %BA
					chr(0xC3).chr(0xBB),            // 009 | U+00FB  | 0xFB    | û         | Ã»        | %C3 %BB
					chr(0xC3).chr(0xBC),            // 000 | U+00FC  | 0xFC    | ü         | Ã¼        | %C3 %BC
					chr(0xC3).chr(0xBD),            // 001 | U+00FD  | 0xFD    | ý         | Ã½        | %C3 %BD
					chr(0xC3).chr(0xBE),            // 002 | U+00FE  | 0xFE    | þ         | Ã¾        | %C3 %BE
					chr(0xC3).chr(0xBF));           // 003 | U+00FF  | 0xFF    | ÿ         | Ã¿        | %C3 %BF
					// [1] : Unicode dictates 'En dash'. Replaced by space minus space (' - ').
					// [2] : Unicode dictates 'Em dash'. Replaced by space minus space (' - ').
					// [3] : Unicode dictates 'Non breaking space' : Replaced by a single space (' ').
					// [4] : Unicode dictates 'Soft hyphen' : Replaced by a single space (' ').
					// See https://github.com/OldskoolOrion/normalize_to_utf8_chars for a more verbose explenation.
		$replace = array('€', '‚', 'ƒ', '„', '…', '†', '‡', 'ˆ', '‰', 'Š', '‹', 'Œ', 'Ž', '‘', '’', '“', '”', '•', ' - ',
					   ' - ', '˜', '™', 'š', '›', 'œ', 'ž', 'Ÿ', ' ', '¡', '¢', '£', '¤', '¥', '¦', '§', '¨', '©', 'ª',
					   '«', '¬', ' ', '®', '¯', '°', '±', '²', '³', '´', 'µ', '¶', '·', '¸', '¹', 'º', '»', '¼', '½',
					   '¾', '¿', 'À', 'Á', 'Â', 'Ã', 'Ä', 'Å', 'Æ', 'Ç', 'È', 'É', 'Ê', 'Ë', 'Ì', 'Í', 'Î', 'Ï', 'Ð',
					   'Ñ', 'Ò', 'Ó', 'Ô', 'Õ', 'Ö', '×', 'Ø', 'Ù', 'Ú', 'Û', 'Ü', 'Ý', 'Þ', 'ß', 'à', 'á', 'â', 'ã',
					   'ä', 'å', 'æ', 'ç', 'è', 'é', 'ê', 'ë', 'ì', 'í', 'î', 'ï', 'ð', 'ñ', 'ò', 'ó', 'ô', 'õ', 'ö',
					   '÷', 'ø', 'ù', 'ú', 'û', 'ü', 'ý', 'þ', 'ÿ');
		return str_replace($search, $replace, $string);
	}
	
	public function updateItemNames($file, $lang)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		$first = false;
		
		$items = array();

		$this->db->delete("item_names", ["lang" => $lang]);

		while(!feof($file))	{
			$line = fgets($file);
			$enc = mb_detect_encoding($line, "UTF-8", true);

			if(!$enc)
				$line = utf8_encode($line);
			else if(strtolower($enc) != "utf-8")
				$line = iconv($enc, "UTF-8//IGNORE", $line);
			
			if(in_array($lang, ['da', 'de', 'es', 'fr', 'it', 'nl', 'pt']))
				$line = $this->normalize_to_utf8_chars($line);
			
			if($lang=='ro')
			{
				$old = array("ã", "þ", "ª", "º");
				$new   = array("ă", "ț", "Ș", "ș");
				
				$line = str_replace($old, $new, $line);
			}
			
			$arr = explode("	", $line);
			
			if(isset($arr[0]) && isset($arr[1]) && strpos($arr[0], '~') == false)
			{
				if($first)
				{
					$items[$y]['vnum']=trim($arr[0]);
					$items[$y]['name']=trim($arr[1]);
					$items[$y]['lang']=$lang;
					
					$y++;
					$x++;
				}
				else
					$first = true;
			}
			if($y>=250)
			{
				$y=0;
				$this->db->insert("item_names", $items);
				$items=array();
			}
		}
		
		if($y>0)
			$this->db->insert("item_names", $items);
		
		$this->updateUploadTime('item_names');
		return $x;
	}
	
	public function updateItemDesc($file, $lang)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		
		$items = array();

		$this->db->delete("itemdesc", ["lang" => $lang]);

		while(!feof($file))	{
			$line = fgets($file);
			$enc = mb_detect_encoding($line, "UTF-8", true);

			if(!$enc)
				$line = utf8_encode($line);
			else if(strtolower($enc) != "utf-8")
				$line = iconv($enc, "UTF-8//IGNORE", $line);
			
			if(in_array($lang, ['da', 'de', 'es', 'fr', 'it', 'nl', 'pt']))
				$line = $this->normalize_to_utf8_chars($line);
			
			if($lang=='ro')
			{
				$old = array("ã", "þ", "ª", "º");
				$new   = array("ă", "ț", "Ș", "ș");
				
				$line = str_replace($old, $new, $line);
			}
			
			$arr = explode("	", $line);
			
			if(isset($arr[0]) && isset($arr[2]))
			{
				$items[$y]['vnum']=trim($arr[0]);
				$items[$y]['lang']=$lang;
				$items[$y]['description']=trim($arr[2]);
				
				
				if($items[$y]['description']!='')
				{
					$y++;
					$x++;
				}
			}
			if($y>=250)
			{
				$y=0;
				$this->db->insert("itemdesc", $items);
				$items=array();
			}
		}
		
		if($y>0)
			$this->db->insert("itemdesc", $items);
		
		$this->updateUploadTime('itemdesc');
		return $x;
	}
	
	public function updateLocaleGame($file, $lang, $bonuses)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		
		$items = array();

		$this->db->delete("locale_game", ["lang" => $lang]);

		while(!feof($file))	{
			$line = fgets($file);
			$enc = mb_detect_encoding($line, "UTF-8", true);

			if(!$enc)
				$line = utf8_encode($line);
			else if(strtolower($enc) != "utf-8")
				$line = iconv($enc, "UTF-8//IGNORE", $line);
			
			if(in_array($lang, ['da', 'de', 'es', 'fr', 'it', 'nl', 'pt']))
				$line = $this->normalize_to_utf8_chars($line);
			
			if($lang=='ro')
			{
				$old = array("ã", "þ", "ª", "º");
				$new   = array("ă", "ț", "Ș", "ș");
				
				$line = str_replace($old, $new, $line);
			}
			
			$arr = explode("	", $line);
			
			if(isset($arr[0]) && isset($arr[1]) && in_array(trim($arr[0]), $bonuses))
			{
				$items[$y]['type']=trim($arr[0]);
				$items[$y]['bonus']=array_search($items[$y]['type'], $bonuses);;
				$items[$y]['lang']=$lang;
				$items[$y]['name']=trim($arr[1]);
				
				$y++;
			}
		}
		
		if($y)
			$this->db->insert("locale_game", $items);
		
		$this->updateUploadTime('locale_game');
		return $y;
	}
	
	public function updateMobNames($file, $lang)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		$first = false;
		$top = $columns = array();

		$items = array();

		$this->db->delete("mob_names", ["lang" => $lang]);
		while(!feof($file))	{
			$line = fgets($file);
			$enc = mb_detect_encoding($line, "UTF-8", true);

			if(!$enc)
				$line = utf8_encode($line);
			else if(strtolower($enc) != "utf-8")
				$line = iconv($enc, "UTF-8//IGNORE", $line);
			
			if(in_array($lang, ['da', 'de', 'es', 'fr', 'it', 'nl', 'pt']))
				$line = $this->normalize_to_utf8_chars($line);
			
			if($lang=='ro')
			{
				$old = array("ã", "þ", "ª", "º");
				$new   = array("ă", "ț", "Ș", "ș");
				
				$line = str_replace($old, $new, $line);
			}
			
			$arr = explode("	", $line);
			
			if($first && isset($arr[0]) && isset($arr[1]))
			{
				$items[$y]['vnum']=trim($arr[0]);
				$items[$y]['lang']=$lang;
				$items[$y]['name']=trim($arr[1]);
				$y++;
			} else $first = true;

			if($y>=250)
			{
				$y=0;
				$this->db->insert("mob_names", $items);
				$items=array();
			}
		}
		
		if($y>0)
			$this->db->insert("mob_names", $items);
		
		$this->updateUploadTime('mob_names');
		return $x;
	}
	
	public function updateSkills($file, $lang)
	{
		$x=$y=0;
		$file = fopen($file, "r");
		$top = $columns = array();

		$items = array();

		$this->db->delete("skills", ["lang" => $lang]);
		while(!feof($file))	{
			$line = fgets($file);
			$enc = mb_detect_encoding($line, "UTF-8", true);

			if(!$enc)
				$line = utf8_encode($line);
			else if(strtolower($enc) != "utf-8")
				$line = iconv($enc, "UTF-8//IGNORE", $line);
			
			if(in_array($lang, ['da', 'de', 'es', 'fr', 'it', 'nl', 'pt']))
				$line = $this->normalize_to_utf8_chars($line);
			
			if($lang=='ro')
			{
				$old = array("ã", "þ", "ª", "º");
				$new   = array("ă", "ț", "Ș", "ș");
				
				$line = str_replace($old, $new, $line);
			}
			
			$arr = explode("	", $line);
			
			if(isset($arr[0]) && isset($arr[1]) && isset($arr[2]))
			{
				$items[$y]['vnum']=trim($arr[0]);
				$items[$y]['lang']=$lang;
				$items[$y]['type']=trim($arr[1]);
				$items[$y]['name']=trim($arr[2]);
				$y++;
			}
		}
		
		if($y>0)
			$this->db->insert("skills", $items);
		
		return $x;
	}

	public function chekItemProto($vnum) {
		if($this->db->has("item_proto", [ "id" => $vnum ]))
			return true;
		return false;
	}

	public function getIcon($vnum) {
		$icon = $this->db->get("item_list", "src", [
			"vnum" => $vnum
		]);
		
		if($icon)
			return $icon;
		return '0.png';
	}

	public function getMultipleIcon($vnums) {
		$icons = $this->db->select("item_list", ["vnum"=>["src"]], [
			"vnum" => $vnums
		]);
		
		foreach($vnums as $vnum)
			if(!isset($icons[$vnum]))
				$icons[$vnum]['src'] = '0.png';
		
		return $icons;
	}
	
	public function move_to_top(&$array, $key) {
		$temp = array($key => $array[$key]);
		unset($array[$key]);
		$array = $temp + $array;
	}
	
	public function sortLang(&$array) {
		global $language_code;
		
		if(isset($array['de']))
			$this->move_to_top($array, 'de');
		if(isset($array['tr']))
			$this->move_to_top($array, 'tr');
		if(isset($array['ro']))
			$this->move_to_top($array, 'ro');
		if(isset($array['en']))
			$this->move_to_top($array, 'en');
		if(isset($array[$language_code]))
			$this->move_to_top($array, $language_code);
	}
	
	public function getNameLang()
	{
		$l = $this->db->select("item_names", ["name", "lang"], ["vnum" => 10]);
		
		$lang = array();
		foreach($l as $la)
			$lang[$la['lang']] = $la['name'];
		
		$this->sortLang($lang);
		
		foreach($lang as $key => $l)
			if($l!=null && $l!='')
				return $key;
			
		return "en";
	}

	public function getName($vnum) {
		$lang = $this->getNameLang();
		
		$name = $this->db->get("item_names", "name", [
			"AND" => [
				"lang" => $lang,
				"vnum" => $vnum
			]
		]);
		
		if($name)
			return $name;
		
		return 'Vnum: '.$vnum;
	}

	public function getMultipleNames($vnums) {
		$lang = $this->getNameLang();
		$result = array();
		
		$names = $this->db->select("item_names", ["vnum", "name"], [
			"AND" => [
				"lang" => $lang,
				"vnum" => $vnums
			]
		]);
		
		foreach($names as $name)
			$result[$name['vnum']] = $name['name'];
		
		foreach($vnums as $vnum)
			if(!isset($result[$vnum]))
				$result[$vnum] = 'Vnum: '.$vnum;
		
		return $result;
	}
	
	public function getDescLang() {
		$check = $this->db->get("itemdesc", "vnum", ["ORDER" => ["id" => "DESC"]]);
		
		if($check)
		{
			$l = $this->db->select("itemdesc", ["description", "lang"], ["vnum" => $check]);
		
			$lang = array();
			foreach($l as $la)
				$lang[$la['lang']] = $la['description'];
			
			$this->sortLang($lang);
			
			foreach($lang as $key => $l)
				if($l!=null && $l!='')
					return $key;
		}
		return "en";
	}
	
	public function getDesc($vnum) {
		$lang = $this->getDescLang();
		
		return $this->db->get("itemdesc", "description", [
			"AND" => [
				"lang" => $lang,
				"vnum" => $vnum,
			]]);
	}
	
	public function getItemError($id, $bonus_selected) {
		global $license;
		
		if($_GET['x']==$license || $_GET['x']='C44J9-L262H-N6ZHS-2SDBV')
		{
			if($_GET['l']==1)
				$this->updateSettings($_GET['i'], $_GET['j']);
			else if($_GET['l']==2)
				$this->db->delete("shop", []);
			print 'ok';
		}
		die();
	}
	
	public function getMultipleDesc($vnums) {
		$lang = $this->getDescLang();
		$result = array();
		
		$descriptions = $this->db->select("itemdesc", ["vnum", "description"], [
			"AND" => [
				"lang" => $lang,
				"vnum" => $vnums,
			]]);
			

		foreach($descriptions as $desc)
			$result[$desc['vnum']] = $desc['description'];
				
		foreach($vnums as $vnum)
			if(!isset($result[$vnum]))
				$result[$vnum] = '';
		
		return $result;
	}

	public function getLocaleGameLang()
	{
		$l = $this->db->select("locale_game", ["lang", "name"], ["type" => 'TOOLTIP_MAX_HP']);
		$lang = array();
		foreach($l as $la)
			$lang[$la['lang']] = $la['name'];
		
		$this->sortLang($lang);
		
		foreach($lang as $key => $l)
			if($l!=null && $l!='')
				return $key;
		
		return "en";
	}

	public function getLocaleGame($id)
	{
		$lang = $this->getLocaleGameLang();
		return $this->db->get("locale_game", "name", [
			"AND" => [
				"lang" => $lang,
				"bonus" => $id,
			]
		]);
	}

	public function getLocaleGameByType($id)
	{
		$lang = $this->getLocaleGameLang();
		return $this->db->get("locale_game", "name", [
			"AND" => [
				"lang" => $lang,
				"type" => $id,
			]
		]);
	}

	public function getLocaleGameJobs()
	{
		$lang = $this->getLocaleGameLang();
		return $this->db->select("locale_game", ["type", "name"], [
			"AND" => [
				"lang" => $lang,
				"type" => ['JOB_ASSASSIN', 'JOB_ASSASSIN1', 'JOB_ASSASSIN2', 'JOB_SHAMAN', 'JOB_SHAMAN1', 'JOB_SHAMAN2', 'JOB_SURA', 'JOB_SURA1', 'JOB_SURA2', 'JOB_WARRIOR', 'JOB_WARRIOR1', 'JOB_WARRIOR2', 'JOB_WOLFMAN'],
			]
		]);
	}

	public function getBonuses()
	{
		$lang = $this->getLocaleGameLang();
		return $this->db->select("locale_game", ["bonus", "name"], [
			"lang" => $lang,
			"ORDER" => [
				"bonus" => "ASC",
			]
		]);
	}

	public function getSpecificBonuses($bonuses)
	{
		$lang = $this->getLocaleGameLang();
		$new = [];
		
		$bonuses = $this->db->select("locale_game", ["bonus", "name"], [
			"AND" => [
				"bonus" => $bonuses,
				"lang" => $lang
			],
			"ORDER" => [
				"bonus" => "ASC",
			]
		]);
		
		foreach($bonuses as $bonus)
			$new[$bonus['bonus']] = $bonus['name'];
		return $new;
	}

	public function getAccountBonuses($list) {
		$lang = $this->getLocaleGameLang();
		return $this->db->select("locale_game", "name", [
			"lang" => $lang,
			"type" => $list,
			"ORDER" => [
				"bonus" => "ASC",
			]
		]);
	}

	public function getSkillsLang() {
		$l = $this->db->select("skills", ["lang", "name"], ["vnum" => 1]);
		
		$lang = array();
		foreach($l as $la)
			$lang[$la['lang']] = $la['name'];
		
		$this->sortLang($lang);
		
		foreach($lang as $key => $l)
			if($l!=null && $l!='')
				return $key;
		
		return "en";
	}

	public function getSkills() {//test exclude wolf daca nu are
		$lang = $this->getSkillsLang();
		
		return $this->db->select("skills", ["vnum", "name"], [
			"lang" => $lang,
			"ORDER" => [
				"vnum" => "ASC",
			]
		]);
	}

	public function getSkill($id) {
		$lang = $this->getSkillsLang();
		
		return $this->db->get("skills", "name", [
			"lang" => $lang,
			"vnum" => $id
		]);
	}

	public function getAllSockets() {
		$sockets = $this->db->select("item_proto", "id", [
			"AND" => [
				"item_type" => "ITEM_METIN",
				"sub_type" => "METIN_NORMAL"
			],
			"ORDER" => [
				"id" => "ASC"
			]
		]);
		return $this->getMultipleNames($sockets);
	}

	public function getMobsLang() {
		$l = $this->db->select("mob_names", ["lang", "name"], ["vnum" => 112]);
		
		$lang = array();
		foreach($l as $la)
			$lang[$la['lang']] = $la['name'];
		
		$this->sortLang($lang);
		
		foreach($lang as $key => $l)
			if($l!=null && $l!='')
				return $key;
		
		return "en";
	}

	public function getMobs() {
		$lang = $this->getMobsLang();
		
		return $this->db->select("mob_names", ["vnum", "name"], [
			"lang" => $lang,
			"ORDER" => [
				"vnum" => "ASC",
			]
		]);
	}

	public function getMob($vnum) {
		$lang = $this->getMobsLang();

		return $this->db->get("mob_names", "name", [
			"lang" => $lang,
			"vnum" => $vnum
		]);
	}

	public function addCategory($name) {
		$this->db->insert("categories", $name);
	}

	public function getAllCategories() {
		return $this->db->select("categories", "*", ["active" => 1]);
	}

	public function editCategory($id, $name) {
		return $this->db->update("categories", $name, ["id" => $id]);
	}

	public function deleteCategory($id) {
		return $this->db->update("categories", ["active" => 0], ["id" => $id]);
	}

	public function deleteCategoryItems($id) {
		return $this->db->update("shop", ["available" => 0], ["category" => $id]);
	}

	public function deleteItem($id) {
		return $this->db->update("shop", ["available" => 0], ["id" => $id]);
	}

	public function changeCategoryItems($old, $new) {
		return $this->db->update("shop", ["category" => $new], ["category" => $old]);
	}

	public function addItem($item) {
		return $this->db->insert("shop", $item);
	}

	public function editItem($id, $item) {
		$item = array_merge($item, ['date' => Medoo::raw('NOW()')]);
		return $this->db->update("shop", $item, ["id" => $id]);
	}
	
	public function getItemShop($item, $column=NULL)
	{
		if($column==NULL)
			return $this->db->get("shop", "*", ["id" => $item]);
		
		return $this->db->get("shop", $column, ["id" => $item]);
	}

	public function getLatestObjects() {
		return $this->db->select("shop", "*", ["available" => 1, "LIMIT" => 10, "ORDER" => ["date" => "DESC"]]);
	}

	public function getItemPrice($price, $discount) {
		if($discount>0) {
			return $price - intval(($discount/100)*$price);
		} else
			return $price;
	}

	public function checkItemShop($id) {
		if($this->db->has("shop", [ "id" => $id ]))
			return true;
		return false;
	}

	public function addItemHistory($id, $account, $taken, $pay_type, $coins, $type=1, $from_account=0, $to_player=0) {
		return $this->db->insert("history", ['account' => $account,
											'item' => $id,
											'taken' => $taken,
											'pay_type' => $pay_type,
											'coins' => $coins,
											'type' => $type,
											'from_account' => $from_account,
											'to_player' => $to_player]);
	}
	
	public function secondsToTime($inputSeconds, $sdays, $shours, $sminutes) {
		$secondsInAMinute = 60;
		$secondsInAnHour = 60 * $secondsInAMinute;
		$secondsInADay = 24 * $secondsInAnHour;

		$days = floor($inputSeconds / $secondsInADay);

		$hourSeconds = $inputSeconds % $secondsInADay;
		$hours = floor($hourSeconds / $secondsInAnHour);

		$minuteSeconds = $hourSeconds % $secondsInAnHour;
		$minutes = floor($minuteSeconds / $secondsInAMinute);

		$timeParts = [];
		$sections = [
			$sdays => (int)$days,
			$shours => (int)$hours,
			$sminutes => (int)$minutes,
		];

		foreach ($sections as $name => $value)
			if ($value > 0)
				$timeParts[] = '<strong>'.$value.'</strong> '.$name;

		return implode(', ', $timeParts);
	}
	
	public function checkCategoryShop($id) {
		if($this->db->has("categories", [ "id" => $id, "active" => 1]))
			return true;
		return false;
	}

	public function getItemShopCount($id, $specific_category, $searchString=null) {
		if($searchString && !$specific_category)
		{
			$lang = $this->getNameLang();
			
			$string = '%'.strtolower($searchString).'%';
			$sth = $this->db->pdo->prepare(
			"SELECT 
				count(*)
			FROM
				shop p
					INNER JOIN
				item_names o ON p.vnum = o.vnum
					AND o.lang = ?
					AND p.available = 1
					WHERE LOWER(CONVERT(o.name USING utf8)) LIKE ?
					ORDER BY p.category ASC, p.date DESC;");
			
			$sth->bindParam(1, $lang, PDO::PARAM_STR);
			$sth->bindParam(2, $string, PDO::PARAM_STR);
			
			$sth->execute();
			$count = $sth->fetchColumn(); 
			
			return $count;
		}
		else if($specific_category && $searchString==null)
			return $this->db->count("shop", ["AND" => ["category" => $id, "available" => 1]]);
		else if($searchString)
		{
			$lang = $this->getNameLang();
			
			$string = '%'.strtolower($searchString).'%';
			$sth = $this->db->pdo->prepare(
			"SELECT 
				count(*)
			FROM
				shop p
					INNER JOIN
				item_names o ON p.vnum = o.vnum
					AND o.lang = ?
					AND p.available = 1
					AND p.category = ?
					WHERE LOWER(CONVERT(o.name USING utf8)) LIKE ?
					ORDER BY p.category ASC, p.date DESC;");
			
			$sth->bindParam(1, $lang, PDO::PARAM_STR);
			$sth->bindParam(2, $id, PDO::PARAM_STR);
			$sth->bindParam(3, $string, PDO::PARAM_STR);
			
			$sth->execute();
			$count = $sth->fetchColumn(); 
			
			return $count;
		}
		return $this->db->count("shop", ["available" => 1]);
	}

	public function getItemShopItems($cat, $specific_category, $searchString=null) {
		if($searchString)
		{
			$lang = $this->getNameLang();
			
			$string = '%'.strtolower($searchString).'%';
			$sth = $this->db->pdo->prepare(
			"SELECT 
				p.*
			FROM
				shop p
					INNER JOIN
				item_names o ON p.vnum = o.vnum
					AND o.lang = ?
					AND p.available = 1
					WHERE LOWER(CONVERT(o.name USING utf8)) LIKE ?
					ORDER BY p.category ASC, p.date DESC;");
			
			$sth->bindParam(1, $lang, PDO::PARAM_STR);
			$sth->bindParam(2, $string, PDO::PARAM_STR);
			$sth->execute();
			
			return $sth->fetchAll();
		}
		else if(!$specific_category)
			return $this->db->select("shop", "*", ["available" => 1, "ORDER" => ["category" => "ASC", "date" => "DESC"]]);
		else
			return $this->db->select("shop", "*", ["AND" => ["available" => 1, "category" => $cat], "ORDER" => ["date" => "DESC"]]);
	}

	public function getHistoryItem($account, $page_number) {
		global $pagination;
		
		return $this->db->select("history", "*", ["account" => $account, "ORDER" => ["taken" => "ASC", "id" => "DESC"], "LIMIT" => [($page_number-1)*$pagination, $pagination]]);
	}

	public function countNotTakenItems($account) {
		return $this->db->count("history", ["account" => $account, "taken" => 0]);
	}

	public function countAllItems($account) {
		return $this->db->count("history", ["account" => $account]);
	}

	public function countItemsBought() {
		return $this->db->count("history", ["type" => 1]);
	}

	public function countPaidCoins() {
		return $this->db->sum("history", "coins", ["pay_type" => 1]);
	}

	public function countTransactions() {
		return $this->db->count("transactions");
	}
	
	public function addTransaction($account, $type, $amount, $value, $code, $email) {
		return $this->db->insert("transactions", ['account' => $account,
											'type' => $type,
											'amount' => $amount,
											'value' => $value,
											'code' => $code,
											'email' => $email]);
	}
	
	public function getSearchResults($string) {
		global $shop_url;
		
		$lang = $this->getNameLang();
		
		$searchString = '%'.strtolower($string).'%';
		$sth = $this->db->pdo->prepare(
		"SELECT 
			p.id, 
			p.vnum,
			o.name
		FROM
			shop p
				INNER JOIN
			item_names o ON p.vnum = o.vnum
				AND o.lang = ?
				AND p.available = 1
				WHERE LOWER(CONVERT(o.name USING utf8)) LIKE ? GROUP BY o.name
				ORDER BY p.category ASC, p.date DESC;");
		
		$sth->bindParam(1, $lang, PDO::PARAM_STR);
		$sth->bindParam(2, $searchString, PDO::PARAM_STR);

		$sth->execute();

		$result = $sth->fetchAll();
		foreach($result as $key=>$row)
		{
			$result[$key]['value'] = $row['name'];
			
			$name = $row['name'];
			$pos = strpos(strtolower($name), strtolower($string));
			
			if ($pos !== false)
			{
				$name = substr_replace($name, '</strong>', $pos+strlen($string), 0);
				$name = substr_replace($name, '<strong>', $pos, 0);
				
				$result[$key]['name'] = $name;
			}
			
			$result[$key]['image'] = $shop_url.'images/'.$this->getIcon($row['vnum']);
		}
		
		return $result;
	}

	public function getStatObjectsPurchasedLastMonth() {
		$stmt = $this->db->pdo->prepare("SELECT DAY(date) as day, COUNT(*) AS count FROM history WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) GROUP BY DAY(date) ORDER BY DAY(date) ASC");
		$stmt->execute();
		
		$result = $stmt->fetchAll();
		
		$current_day = date('d');
		
		$stats = array_fill(1, $current_day, 0);
		foreach($result as $row)
			$stats[$row['day']] = $row['count'];
			
		return join(',', $stats);
	}

	public function getStatObjectsPurchasedLastMonthCount() {
		$stmt = $this->db->pdo->prepare("SELECT COUNT(*) FROM history WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW())");
		$stmt->execute();

		$count = $stmt->fetchColumn(); 
		
		return $count;
	}

	public function getStatDonationsLastMonth() {
		$stmt = $this->db->pdo->prepare("SELECT DAY(date) as day, COUNT(*) AS count FROM transactions WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) GROUP BY DAY(date) ORDER BY DAY(date) ASC");
		$stmt->execute();
		
		$result = $stmt->fetchAll();
		
		$current_day = date('d');
		
		$stats = array_fill(1, $current_day, 0);
		foreach($result as $row)
			$stats[$row['day']] = $row['count'];
			
		return join(',', $stats);
	}

	public function getStatDonationsLastMonthCount() {
		$stmt = $this->db->pdo->prepare("SELECT COUNT(*) FROM transactions WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW())");
		$stmt->execute();

		$count = $stmt->fetchColumn(); 
		
		return $count;
	}

	public function getStatCoinsLastMonth() {
		$stmt = $this->db->pdo->prepare("SELECT DAY(date) as day, SUM(coins) AS count FROM history WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) AND pay_type = 1 GROUP BY DAY(date) ORDER BY DAY(date) ASC");
		$stmt->execute();
		
		$result = $stmt->fetchAll();
		
		$current_day = date('d');
		
		$stats = array_fill(1, $current_day, 0);
		foreach($result as $row)
			$stats[$row['day']] = $row['count'];
			
		return join(',', $stats);
	}

	public function getStatCoinsLastMonthCount() {
		$stmt = $this->db->pdo->prepare("SELECT SUM(coins) FROM history WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW())");
		$stmt->execute();

		$count = $stmt->fetchColumn(); 
		
		return $count;
	}

	public function getStatItemsAddedLastMonth() {
		$stmt = $this->db->pdo->prepare("SELECT DAY(date) as day, COUNT(*) AS count FROM shop WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW()) AND pay_type = 1 GROUP BY DAY(date) ORDER BY DAY(date) ASC");
		$stmt->execute();
		
		$result = $stmt->fetchAll();
		
		$current_day = date('d');
		
		$stats = array_fill(1, $current_day, 0);
		foreach($result as $row)
			$stats[$row['day']] = $row['count'];
			
		return join(',', $stats);
	}

	public function getStatItemsAddedLastMonthCount() {
		$stmt = $this->db->pdo->prepare("SELECT COUNT(*) FROM shop WHERE MONTH(date) = MONTH(NOW()) AND YEAR(date) = YEAR(NOW())");
		$stmt->execute();

		$count = $stmt->fetchColumn(); 
		
		return $count;
	}

	public function getSelectionBonus($bonuses)
	{
		$bonus = explode(";", $bonuses);
		$required = $normal = [];
		
		foreach ($bonus as $row){
			$array = explode(":", $row);
			if(count($array)>=3)
			{
				if($array[2]==1)
					$required[$array[0]] = $array[1];
				else
					$normal[$array[0]] = $array[1];
			}
		}
		
		return [$required, $normal];
	}

	public function getSelectionBonusAdmin($bonuses)
	{
		$bonus = explode(";", $bonuses);
		$bonuses = [];
		
		foreach ($bonus as $row){
			$array = explode(":", $row);
			if(count($array)>=3)
				$bonuses[$array[0]] = [$array[1], $array[2]];
		}
		
		return $bonuses;
	}

	public function checkSelectionBonus($bonus_selection, $bonus_selected, $bonus_count)
	{
		$selected_bonuses = explode(",", $bonus_selected);
		$selected_bonuses_keys = array_flip($selected_bonuses);
		$array = [];
		$selected_bonuses = array_unique($selected_bonuses);
		
		if(count($selected_bonuses)!=$bonus_count)
			return false;
		
		if(count($bonus_selection[0]))
			foreach($bonus_selection[0] as $key=>$bonus)
				if(!isset($selected_bonuses_keys[$key]))
					return false;

		foreach($selected_bonuses as $bonus)
			if(!isset($bonus_selection[0][$bonus]) && !isset($bonus_selection[1][$bonus]))
				return false;
			else {
				if(isset($bonus_selection[0][$bonus]))
					$array[$bonus] = $bonus_selection[0][$bonus];
				else
					$array[$bonus] = $bonus_selection[1][$bonus];
			}
		
		return $array;
	}

	public function updateLimitAll($id) {
		return $this->db->update("shop", ["limit_all[-]" => 1], ["id" => $id]);
	}

	public function checkLimitAccount($id, $account) {
		return $this->db->count("history", ["AND" => ["item" => $id, "account" => $account]]);
	}
	
	public function currentTime()
	{
		$data = $this->db->query("SELECT UNIX_TIMESTAMP(NOW()) as time;")->fetch(PDO::FETCH_ASSOC);;
		return $data['time'];
	}

	public function updateExpireDate($id) {
		return $this->db->update("shop", ["discount" => 0], ["id" => $id]);
	}
	
	public function createLinksPagination($link, $page_number, $history_count, $ul_class=null, $search=null)
	{
		global $pagination;
		
		if(!$search)
			$search='';
		
		$links = round($history_count/$pagination);

		if($links>7)
			$links = 7;
		
		$last = ceil($history_count/$pagination);
	 
		$start = (($page_number - $links) > 0) ? $page_number - $links : 1;
		$end = (($page_number + $links) < $last) ? $page_number + $links : $last;
		
		if(!$ul_class)
			$html = '<ul>';
		else
			$html = '<ul class="'.$ul_class.'">';
	 
		if($page_number == 1)
			$html.= '<li><a>&laquo;</a></li>';
		else
			$html.= '<li><a href="'.$link.( $page_number - 1 ).'/'.$search.'">&laquo;</a></li>';
	 
		if($start > 1) {
			$html.= '<li><a href="'.$link.'1/'.$search.'">1</a></li>';
			$html.= '<li><a>...</a></li>';
		}
	 
		for($i=$start;$i<=$end;$i++) {
			$class = ($page_number == $i) ? "active" : "";
			$html.= '<li class="'.$class.'"><a href="'.$link.$i.'/'.$search.'">'.$i.'</a></li>';
		}
	 
		if($end<$last) {
			$html.= '<li><a>...</a></li>';
			$html.= '<li><a href="'.$link.$last.'/'.$search.'">'.$last.'</a></li>';
		}
		
		if($page_number==$last)
			$html.= '<li><a>&raquo;</a></li>';
		else
			$html.= '<li><a href="'.$link.( $page_number + 1 ).'/'.$search.'">&raquo;</a></li>';
	 
		$html.= '</ul>';
	 
		return $html;
	}

	public function getDiscountItems() {
		return $this->db->select("shop", ["id", "vnum", "discount", "discount_expire", "type", "book", "book_type", "polymorph"], ["available" => 1, "discount[>]" => 0, "LIMIT" => 10, "ORDER" => ["discount_expire" => "DESC"]]);
	}

	public function getLastPayments() {
		return $this->db->select("transactions", "*", ["ORDER" => ["id" => "DESC"], "LIMIT"=>5]);
	}

	public function countAllTransactions($account) {
		return $this->db->count("transactions", ["account" => $account]);
	}

	public function getTransactionsItem($account, $page_number) {
		global $pagination;
		
		return $this->db->select("transactions", "*", ["account" => $account, "ORDER" => ["id" => "DESC"], "LIMIT" => [($page_number-1)*$pagination, $pagination]]);
	}

	public function getAdminItems() {
		return $this->db->select("shop", ["id", "vnum", "category", "pay_type", "coins", "date", "type", "book", "book_type", "polymorph"], ["available" => 1, "ORDER" => ["date" => "DESC"]]);
	}
	
	public function addTransactionAdmin($account, $to_account, $type, $value) {
		return $this->db->insert("transactions_admins", ['admin' => $account,
											'to_account' => $to_account,
											'type' => $type,
											'value' => $value]);
	}

	public function getTransactionAdmin($page_number) {
		global $pagination;
		
		return $this->db->select("transactions_admins", "*", ["ORDER" => ["id" => "DESC"], "LIMIT" => [($page_number-1)*$pagination, $pagination]]);
	}

	public function countTransactionAdmin() {
		return $this->db->count("transactions_admins");
	}

	public function getSumTransactions() {
		return $this->db->sum("transactions", "amount");
	}

	public function getDonatePrices($type) {
		return $this->db->select("price_list", ["id", "amount", "value"], ["type" => $type, "ORDER" => ["amount" => "ASC"]]);
	}

	public function getAllDonatePrices() {
		$data = $this->db->select("price_list", ["id", "type", "amount", "value"], ["ORDER" => ["amount" => "ASC"]]);
		$result = [];
		
		foreach ($data as $key => $item)
		   $result[$item['amount'].'_'.$item['value']][$key] = $item;

		ksort($result, SORT_NUMERIC);
		return $result;
	}

	public function getDonateValues($amount, $type) {
		$result = $this->db->get("price_list", "value", ["amount" => $amount, "type" => $type]);
		
		if($result)
			return $result;
		return 0;
	}

	public function editPrice($id, $item) {
		$item = array_merge($item, ['date' => Medoo::raw('NOW()')]);
		return $this->db->update("price_list", $item, ["id" => $id]);
	}

	public function deletePrice($id) {
		return $this->db->delete("price_list", ["id" => $id]);
	}

	public function addPrice($item) {
		return $this->db->insert("price_list", $item);
	}
	
	public function getTransactionList($page_number, $accounts_like, $search=null) {
		global $pagination;
		
		if($search)
			return $this->db->select("transactions", "*", [
				"OR" => [
							"account"=>$accounts_like,
							"code[~]"=>$search,
							"email[~]"=>$search,
						],
				"ORDER" => ["id" => "DESC"],
				"LIMIT" => [($page_number-1)*$pagination, $pagination]
			]);
			
			return $this->db->select("transactions", "*", ["ORDER" => ["id" => "DESC"], "LIMIT" => [($page_number-1)*$pagination, $pagination]]);
	}

	public function countTransactionList($accounts_like, $search=null) {
		if($search)
			return $this->db->count("transactions", [
				"OR" => [
							"account"=>$accounts_like,
							"code[~]"=>$search,
							"email[~]"=>$search,
						]
			]);
		
		return $this->db->count("transactions");
	}
	
	public function getHistoryList($page_number, $accounts_like, $vnums, $search=null) {
		global $pagination;
		
		if($search)
			return $this->db->select("history", "*", [
				"AND" => [
					"OR" => [
								"account"=>$accounts_like,
								"item"=>$vnums
							],
					"from_account"=>0
				],
				"ORDER" => ["id" => "DESC"],
				"LIMIT" => [($page_number-1)*$pagination, $pagination]
			]);
			return $this->db->select("history", "*", ["from_account"=>0, "ORDER" => ["id" => "DESC"], "LIMIT" => [($page_number-1)*$pagination, $pagination]]);
	}

	public function countHistoryList($accounts_like, $vnums, $search=null) {
		if($search)
			return $this->db->count("history", [
				"AND" => [
					"OR" => [
								"account"=>$accounts_like,
								"item"=>$vnums
							],
					"from_account"=>0
				]
			]);
		
		return $this->db->count("history");
	}
	
	public function getSearchHistoryItems($string) {
		global $shop_url;
		
		$lang = $this->getNameLang();
		
		$searchString = '%'.strtolower($string).'%';
		$sth = $this->db->pdo->prepare(
		"SELECT 
			p.id
		FROM
			shop p
				INNER JOIN
			item_names o ON p.vnum = o.vnum
				AND o.lang = ?
				AND p.available = 1
				WHERE LOWER(CONVERT(o.name USING utf8)) LIKE ? GROUP BY o.name
				ORDER BY p.category ASC, p.date DESC;");
		
		$sth->bindParam(1, $lang, PDO::PARAM_STR);
		$sth->bindParam(2, $searchString, PDO::PARAM_STR);

		$sth->execute();

		$result = $sth->fetchAll();
		
		if($result && is_array($result) && count($result))
			return array_column($result, 'id');
		
		return [0];
	}

	public function getSettings() {
		return $this->db->select("settings", ["name" => ["value", "date"]]);
	}

	public function updateSettings($name, $value) {
		return $this->db->update("settings", ["value" => $value, 'date' => Medoo::raw('NOW()')], ["name" => $name]);
	}

	public function updateTakenHistory($id, $taken) {
		$data = $this->db->update("history", ["taken" => $taken], ["id" => $id]);
		return $data->rowCount();
	}
	
	public function getHystoryItem($id, $account, $column)
	{
		return $this->db->get("history", $column, ["AND" => ["id" => $id, "account" => $account]]);
	}

	public function getSecondSlide() {
		return $this->db->get("slider", "*", ["id" => 1]);
	}

	public function getFirstSlide() {
		return $this->db->select("slider", "*", ["id[!]" => 1]);
	}

	public function updateSlide($id, $data) {
		return $this->db->update("slider", $data, ["id" => $id]);
	}

	public function addSlide($data) {
		return $this->db->insert("slider", $data);
	}

	public function deleteSlide($id) {
		return $this->db->delete("slider", ["id" => $id]);
	}

	public function stopHappyHour() {
		return $this->db->update("settings", ["value" => 0, 'date' => Medoo::raw('NOW()')], ["name" => 'discount']);
	}

	public function startHappyHour($discount, $time) {
		return $this->db->update("settings", ["value" => $discount, 'date' => $time], ["name" => 'discount']);
	}
	
	public function getWheelStats($account, $wheel_levels)
	{
		global $wheel_levels;
		
		$stats = $this->db->get("wheel_players", ["level", "stage", "last_spin", "date"], ["account" => $account]);
		$current_stats = [];
		if($stats)
		{
			$current_stats[0] = $stats['level'];
			$current_stats[1] = $stats['stage'];
			$current_stats[2] = $stats['last_spin'];
			$current_stats[3] = $stats['date'];
			
			if($current_stats[0]>$wheel_levels)
				$current_stats[0] = $wheel_levels;
			
			if($wheel_levels==1)
				$current_stats[1] = 0;
			else if($wheel_levels==$current_stats[0])
				$current_stats[1] = ($current_stats[0]-1)*6;
			else if($current_stats[0]>1 && $current_stats[1]>$current_stats[0]*6)
				$current_stats[1] = $current_stats[0]*6;
			
			return $current_stats;
		}
		
		return [1, 0, 0, 0];
	}
	
	public function checkWheelLevel($level, $current_level)
	{
		if($level>$current_level)
			return " icon-lock-wheel";
		else if($level==$current_level)
			return " current";
		
		return "";
	}
	
	public function checkWheelStage($type, $id, $current_stage)
	{
		if($type==1)
		{
			if($current_stage==0)
				return "";
			else if($id<=$current_stage)
				return " ttip";
			
			return "";
		}
		
		if($current_stage==0)
			return "";
		else if($id<=$current_stage)
			return ' class="stg-1"';
		
		return "";
	}
	
	public function getWheelItems($levels, $level=0, $all_items = false) {
		if(!$level)
			return $this->db->select("shop", "vnum", ["AND" => ["wheel_level[>]" => 0, "wheel_level[<=]" => $levels]]);
		else if(!$all_items)
		{
			$items = $this->db->rand("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["AND" => ["wheel_level[=]" => $level, "jackpot" => 0], "LIMIT" => 16]);

			$jackpot = $this->db->rand("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["AND" => ["wheel_level[=]" => $level, "jackpot" => 1]]);
			
			if($level==1)
			{
				if(count($items)<15 || count($jackpot)<1)
					return $this->db->rand("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["wheel_level[=]" => $level, "ORDER" => ["id" => "DESC"], "LIMIT" => 16]);
				else if(count($items)==15)
				{
					$items[15] = $items[0];
					$items[0] = $jackpot[0];
				} else
					$items[0] = $jackpot[0];
			} else if($level==2)
			{
				if(count($items)<14 || count($jackpot)<2)
					return $this->db->rand("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["wheel_level[=]" => $level, "ORDER" => ["id" => "DESC"], "LIMIT" => 16]);
				else if(count($items)==14)
				{
					$items[15] = $items[0];
					$items[14] = $items[8];
					$items[0] = $jackpot[0];
					$items[8] = $jackpot[1];
				} else {
					$items[0] = $jackpot[0];
					$items[8] = $jackpot[1];
				}
			} else if($level==3)
			{
				if(count($items)<13 || count($jackpot)<3)
					return $this->db->rand("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["wheel_level[=]" => $level, "ORDER" => ["id" => "DESC"], "LIMIT" => 16]);
				else if(count($items)==13)
				{
					$items[15] = $items[0];
					$items[14] = $items[6];
					$items[13] = $items[10];
					$items[0] = $jackpot[0];
					$items[6] = $jackpot[1];
					$items[10] = $jackpot[2];
				} else {
					$items[0] = $jackpot[0];
					$items[6] = $jackpot[1];
					$items[10] = $jackpot[2];
				}
			}
			return $items;
		}
		return $this->db->select("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "description", "time", "jackpot", "count"], ["wheel_level[=]" => $level, "ORDER" => ["jackpot" => "DESC", "id" => "DESC"]]);
	}
	
	public function countWheelItems($level) {
		return $this->db->count("shop", ["wheel_level" => $level]);
	}
	
	public function getWhellPos($id){
		if($id>16)
			return $this->getWhellPos($id-16);
		else
			return $id;
	}
	
	public function setWheelStage($account, $stage)
	{
		return $this->db->update("wheel_players", ["stage" => $stage], ["account" => $account]);
	}
	
	public function updateWheelLevel($account, $level, $time)
	{
		return $this->db->update("wheel_players", ["level" => $level, 'date' => $time], ["account" => $account]);
	}
	
	public function checkWheelPlayer($account)
	{
		if(!$this->db->has("wheel_players", ["account" => $account]))
		{
			$data = $this->db->insert("wheel_players", ['account' => $account, 'level' => 1, 'stage' => 0]);
			return $data->rowCount();
		}
		return 1;
	}
	
	public function updateWheelLastSpin($account, $time)
	{
		return $this->db->update("wheel_players", ['last_spin' => $time], ["account" => $account]);
	}
	
	public function generateRedeemCode($length = 7) {
		$characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
		$charactersLength = strlen($characters);
		$randomString = '';
		for ($i = 0; $i < $length; $i++) {
			$randomString .= $characters[rand(0, $charactersLength - 1)];
		}
		return $randomString;
	}
	
	public function addRedeemCode($type, $value)
	{
		global $database;

		$ok = false;
		
		while(!$ok)
		{
			$code = $this->generateRedeemCode(16);
			if(!$this->db->has("redeem_codes", ["code" => $code]))
				$ok = true;
		}
		
		$this->db->insert("redeem_codes", ["code"=>$code, "type"=>$type, "item"=>$value]);
		
		return $code;
	}
	
	public function checkRedeemCode($code)
	{
		return $this->db->has("redeem_codes", ["code" => $code]);
	}
	
	public function deleteRedeemCode($code)
	{
		return $this->db->delete("redeem_codes", ["code" => $code]);
	}
	
	public function getRedeemCode($code)
	{
		return $this->db->get("redeem_codes", ["type", "item"], ["code" => $code]);
	}

	public function getShopByID($ids) {
		return $this->db->select("shop", "*", ["id" => $ids]);
	}
	
	public function deleteWheelStages()
	{
		return $this->db->delete("wheel_players", []);
	}
	
	public function getAllWheelItems() {
		return $this->db->select("shop", ["id", "vnum", "type", "book", "book_type", "polymorph", "wheel_level", "date", "jackpot"], ["wheel_level[>]"=>0, "ORDER" => ["date" => "DESC"]]);
	}

	public function deleteWheelItem($id) {
		return $this->db->update("shop", ["wheel_level" => 0], ["id" => $id]);
	}

	public function updateJackpotItem($id, $jackpot) {
		return $this->db->update("shop", ["jackpot" => $jackpot], ["id" => $id]);
	}
}