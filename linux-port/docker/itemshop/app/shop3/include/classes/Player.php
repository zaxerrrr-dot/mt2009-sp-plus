<?php
class Player {

	private $db = NULL, $shop = NULL, $account = NULL, $server_item = [];

	public function __construct($db, $shop, $account, $server_item) {
		$this->db = $db; 
		$this->shop = $shop; 
		$this->account = $account; 
		$this->server_item = $server_item; 
	}

	public function getPlayerData($column, $id)
	{
		return $this->db->get("player", $column, [
			"id" => $id
		]);
	}

	public function GetValue($item_proto, $i)
	{
		return $item_proto['value'.$i];
	}

	public function GetType($item_proto)
	{
		return $item_proto['item_type'];
	}

	public function GetLimitType($item_proto, $i)
	{
		return $item_proto['limit_type'.$i];
	}

	public function GetLimitValue($item_proto, $i)
	{
		return $item_proto['limit_value'.$i];
	}

	public function GetSocket($item_proto, $i)
	{
		return $item_proto['socket'.$i];
	}

	public function GetSize($vnum)
	{
		return $this->shop->getItem($vnum, 'size');
	}
	
	private function getItemColumns()
	{
		return $this->db->query("DESCRIBE item")->fetchAll(PDO::FETCH_COLUMN);
	}
	
	private function getItemAwardColumns()
	{
		return $this->db->query("DESCRIBE item_award")->fetchAll(PDO::FETCH_COLUMN);
	}

	public function GetTItemAttrTable()
	{
		$item_attr = $this->db->select("item_attr", "*");
		
		$array = [];
		foreach($item_attr as $key => $attr)
		{
			$id = array_search('APPLY_'.$attr['apply'], $this->server_item['EApplyTypes']);
			
			$array[$key]['dwApplyIndex'] = $id;
			$array[$key]['dwProb'] = $attr['prob'];
			$array[$key]['lValues'][0] = $attr['lv1'];
			$array[$key]['lValues'][1] = $attr['lv2'];
			$array[$key]['lValues'][2] = $attr['lv3'];
			$array[$key]['lValues'][3] = $attr['lv4'];
			$array[$key]['lValues'][4] = $attr['lv5'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_WEAPON', $this->server_item['EAttributeSet'])] = $attr['weapon'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_BODY', $this->server_item['EAttributeSet'])] = $attr['body'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_WRIST', $this->server_item['EAttributeSet'])] = $attr['wrist'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_FOOTS', $this->server_item['EAttributeSet'])] = $attr['foots'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_NECK', $this->server_item['EAttributeSet'])] = $attr['neck'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_HEAD', $this->server_item['EAttributeSet'])] = $attr['head'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_SHIELD', $this->server_item['EAttributeSet'])] = $attr['shield'];
			$array[$key]['bMaxLevelBySet'][array_search('ATTRIBUTE_SET_EAR', $this->server_item['EAttributeSet'])] = $attr['ear'];
		}
		return $array;
	}
	
	private function FN_random_index()
	{
		$percent = rand(1,100);

		if($percent<=10)			// level 1 :10%
			return 0;
		else if($percent<=30)		// level 2 : 20%
			return 1;
		else if($percent<=70)		// level 3 : 40%
			return 2;
		else if($percent<=90)		// level 4 : 20%
			return 3;
		else
			return 4;				// level 5 : 10%

		return 0;
	}
	
	private function FN_ECS_random_index()
	{
		$percent = rand(1,100);

		if($percent<=5)			// level 1 : 5%
			return 0;
		else if($percent<=15)		// level 2 : 10%
			return 1;
		else if($percent<=60)		// level 3 : 45%
			return 2;
		else if($percent<=85)		// level 4 : 25%
			return 3;
		else
			return 4;				// level 5 : 15%

		return 0;
	}
	
	public function getNewPosition($new_item, $account)
	{
		$result = $this->db->select("item", [
										"pos",
										"vnum"
									], [
										"owner_id" => $account,
										"window" => "MALL",
										"ORDER" => ["pos" => "ASC"],
									]);
		
		$used = $items_used = $used_check = [];
		
		foreach($result as $row ) {
			$used_check[] = $row['pos'];
			$used[$row['pos']] = 1;
			$items_used[$row['pos']] = $row['vnum'];
		}
		$used_check = array_unique($used_check);

		$free = -1;
		
		for($i=0; $i<45; $i++){
			if(!in_array($i,$used_check)){
				$ok = true;
				
				if($i>4 && $i<10)
				{
					if(array_key_exists($i-5, $used) && $this->GetSize($items_used[$i-5])>1)
						$ok = false;
				}
				else if($i>9 && $i<40)
				{
					if(array_key_exists($i-5, $used) && $this->GetSize($items_used[$i-5])>1)
						$ok = false;
					
					if(array_key_exists($i-10, $used) && $this->GetSize($items_used[$i-10])>2)
						$ok = false;
				}
				else if($i>39 && $i<45 && $this->GetSize($new_item)>1)
						$ok = false;
				
				if($ok)
					return $i;
			}
		}
		
		return $free;
	}
	
	private function GetAttribute($aiAttrPercentTable, $item_type, $item_sub_type, $attr_used=[])
	{
		$iAttrLevelPercent = rand(1, 100);

		for ($i = 0; $i < count($aiAttrPercentTable); ++$i)
		{
			if($iAttrLevelPercent <= $aiAttrPercentTable[$i])
				break;

			$iAttrLevelPercent -= $aiAttrPercentTable[$i];
		}

		return $this->PutAttributeWithLevel($i + 1, $item_type, $item_sub_type, $aiAttrPercentTable, $attr_used);
	}
	
	private function PutAttributeWithLevel($bLevel, $item_type, $item_sub_type, $aiAttrPercentTable, $attr_used)
	{
		$iAttributeSet = $this->GetAttributeSetIndex($item_type, $item_sub_type);

		if($iAttributeSet < 0)
			return [0, 0];
		if($bLevel > count($aiAttrPercentTable))
			return [0, 0];
		
		$TItemAttrTable = $this->GetTItemAttrTable();

		$avail = [];
		$total = 0;
		
		for ($i = 0; $i < count($TItemAttrTable); ++$i)
		{
			$r = $TItemAttrTable[$i];

			if($r['bMaxLevelBySet'][$iAttributeSet] && !in_array($r['dwApplyIndex'], $attr_used))
			{
				$avail[]=$i;
				$total += $r['dwProb'];
			}
		}
		
		$prob = rand(1, $total);
		$attr_idx = 0;
		
		for ($i = 0; $i < count($avail); ++$i)
		{
			$r = $TItemAttrTable[$avail[$i]];

			if($prob <= $r['dwProb'])
			{
				$attr_idx = $avail[$i];
				break;
			}

			$prob -= $r['dwProb'];
		}
		
		if(!$attr_idx)
			return [0, 0];

		$r = $TItemAttrTable[$attr_idx];
		
		print $bLevel.'<br>';
		
		if($bLevel > $r['bMaxLevelBySet'][$iAttributeSet])
			$bLevel = $r['bMaxLevelBySet'][$iAttributeSet];
		
		$x = min(4, $bLevel - 1);
		if($x<0)
			$x=0;
		
		$lVal = $r['lValues'][$x];

		if($lVal)
			return [$r['dwApplyIndex'], $lVal];
		
		return [0, 0];
	}
	
	public function GetAttributeSetIndex($item_type, $item_sub_type)
	{
		if($item_type == 'ITEM_WEAPON')
		{
			if($item_sub_type == 'WEAPON_ARROW')
				return -1;

			return array_search('ATTRIBUTE_SET_WEAPON', $this->server_item['EAttributeSet']);
		}

		if($item_type == 'ITEM_ARMOR')
		{
			switch ($item_sub_type)
			{
				case 'ARMOR_BODY':
					return array_search('ATTRIBUTE_SET_BODY', $this->server_item['EAttributeSet']);

				case 'ARMOR_WRIST':
					return array_search('ATTRIBUTE_SET_WRIST', $this->server_item['EAttributeSet']);

				case 'ARMOR_FOOTS':
					return array_search('ATTRIBUTE_SET_FOOTS', $this->server_item['EAttributeSet']);

				case 'ARMOR_NECK':
					return array_search('ATTRIBUTE_SET_NECK', $this->server_item['EAttributeSet']);

				case 'ARMOR_HEAD':
					return array_search('ATTRIBUTE_SET_HEAD', $this->server_item['EAttributeSet']);

				case 'ARMOR_SHIELD':
					return array_search('ATTRIBUTE_SET_SHIELD', $this->server_item['EAttributeSet']);

				case 'ARMOR_EAR':
					return array_search('ATTRIBUTE_SET_EAR', $this->server_item['EAttributeSet']);
			}
		}
		else if($item_type == 'ITEM_COSTUME')
		{
			switch ($item_sub_type)
			{
				case 'COSTUME_BODY':
					return array_search('ATTRIBUTE_SET_BODY', $this->server_item['EAttributeSet']);
				case 'COSTUME_HAIR':
					return array_search('ATTRIBUTE_SET_HEAD', $this->server_item['EAttributeSet']);
				case 'COSTUME_MOUNT':
					break;
				case 'COSTUME_WEAPON':
					return array_search('ATTRIBUTE_SET_WEAPON', $this->server_item['EAttributeSet']);
			}
		}

		return -1;
	}
	

	private function uniform_random($a, $b)
	{
		return rand(0, 32767) / (32767 + 1.0) * ($b - $a) + $a;
	}
	
	private function gauss_random($avg, $sigma)
	{
		$haveNextGaussian = false;
		$nextGaussian = 0.0;
		
		$FLT_EPSILON = 0.0000001192092896;//1.192092896e-07F
		if($haveNextGaussian)
		{
			$haveNextGaussian = false;
			return $nextGaussian * $sigma + $avg;
		}
		else
		{
			do {
				$v1 = $this->uniform_random(-1.0, 1.0);
				$v2 = $this->uniform_random(-1.0, 1.0);
				$s = $v1 * $v1 + $v2 * $v2;
			} while($s >= 1.0 || abs($s) < $FLT_EPSILON);
			$multiplier = sqrt(-2 * log($s)/$s);
			$nextGaussian = $v2 * $multiplier;
			$haveNextGaussian = true;
			return $v1 * $multiplier * $sigma + $avg;
		}
	}
		
	public function MINMAX($min, $value, $max)
	{
		$tv;

		$tv = ($min > $value ? $min : $value);
		return ($max < $tv) ? $max : $tv;
	}

	private function GetAddon($iAddonType)
	{
		$iSkillBonus = 0;
		while(!$iSkillBonus)
			$iSkillBonus = $this->MINMAX(-30, round($this->gauss_random(0, 5) + 0.5), 30);
		$iNormalHitBonus = 0;
		if (abs($iSkillBonus) <= 20)
			$iNormalHitBonus = -2 * $iSkillBonus + abs(rand(-8, 8) + rand(-8, 8)) + rand(1, 4);
		else
			$iNormalHitBonus = -2 * $iSkillBonus + rand(1, 5);
		
		return [$iNormalHitBonus, $iSkillBonus];
	}
	
	public function currentTime()
	{	
		$data = $this->db->query("SELECT UNIX_TIMESTAMP(NOW()) as time;")->fetch(PDO::FETCH_ASSOC);;
		return $data['time'];
	}
	
	public function checkLimitTime($item_proto, $itemType)
	{
		if($itemType == 'ITEM_UNIQUE')
			return true;
		
		for ($i=0 ; $i < $this->server_item['EItemMisc']['ITEM_LIMIT_MAX_NUM']; $i++)
			if('LIMIT_REAL_TIME' == 'LIMIT_'.$this->GetLimitType($item_proto, $i) || 'LIMIT_TIMER_BASED_ON_WEAR' == 'LIMIT_'.$this->GetLimitType($item_proto, $i) || 'LIMIT_REAL_TIME_FIRST_USE' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
				return true;

		return false;
	}
	
	public function CreateItem($item_shop, $account, $add_type='item_award', $selected_bonuses)
	{
		global $wolfman_character;
		
		$vnum = $item_shop['vnum'];
		
		if($add_type=='item_award')
			$item = [
				'login' => $this->account->getAccountData('login', $account),
				'vnum' => $item_shop['vnum'],
				'count' => $item_shop['count'],
				'why' => "Item Shop",
				'socket0' => 0,
				'socket1' => 0,
				'socket2' => 0,
				'mall' => 1
			];
		else
		{
			$item = [
				'vnum' => $item_shop['vnum'],
				'owner_id' => $account,
				'window' => 'MALL',
				'count' => $item_shop['count'],
				'socket0' => 0,
				'socket1' => 0,
				'socket2' => 0
			];
		
			$item['pos'] = $this->getNewPosition($vnum, $account);
			
			if($item['pos']==-1)
				return false;
		}
		$attr_used = [];
		
		$item_proto = $this->shop->getItem($vnum);
		
		if($item_proto)
		{
			for($i=1;$i<=$item_proto['gain_socket'];$i++)
				$item['socket'.($i-1)]=1;
			
			for($i=0;$i<6;$i++)//shop
				if($item_shop['socket'.$i]>0)
					$item['socket'.$i] = $item_shop['socket'.$i];
			
			$itemType = $this->GetType($item_proto);
			
			if($itemType == 'ITEM_UNIQUE')
			{
				if($this->GetValue($item_proto, 2) == 0)
				{
					if($add_type=='item')
						$item['socket'.$this->server_item['EItemUniqueSockets']['ITEM_SOCKET_UNIQUE_REMAIN_TIME']] = $this->GetValue($item_proto, 0);//sec
					
					if($item_shop['time']>0)//shop
						$item['socket'.$this->server_item['EItemUniqueSockets']['ITEM_SOCKET_UNIQUE_REMAIN_TIME']] = $item_shop['time']*60;
				}
				else
				{
					if($add_type=='item')
						$item['socket'.$this->server_item['EItemUniqueSockets']['ITEM_SOCKET_UNIQUE_REMAIN_TIME']] = $this->currentTime() + $this->GetValue($item_proto, 0);

					if($item_shop['time']>0)//shop
						$item['socket'.$this->server_item['EItemUniqueSockets']['ITEM_SOCKET_UNIQUE_REMAIN_TIME']] = $this->currentTime() + $item_shop['time']*60;
				}
			}
			else if($itemType == 'ITEM_POLYMORPH')
				$item['socket0'] = $item_shop['polymorph'];
			/*
			if($itemType == 'ITEM_STACKABLE' && $item['count']>$this->server_item['EItemMisc']['ITEM_MAX_COUNT'])
				$item['count'] = $this->server_item['EItemMisc']['ITEM_MAX_COUNT'];
			else $item['count'] = 1;
			*/
			if($item['count']>$this->server_item['EItemMisc']['ITEM_MAX_COUNT'])
				$item['count'] = $this->server_item['EItemMisc']['ITEM_MAX_COUNT'];
			
			if($add_type=='item')
				foreach($this->server_item['recovery_item'] as $i)
					if($this->server_item['unique_item'][$i]==$vnum)
					{
						$item['socket2'] = $this->GetValue($item_proto, 0);
						break;
					}
			
			for ($i=0 ; $i < $this->server_item['EItemMisc']['ITEM_LIMIT_MAX_NUM']; $i++)
			{
				if('LIMIT_REAL_TIME' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
				{
					if($this->GetLimitValue($item_proto, $i))
					{
						if($add_type=='item')
							$item['socket0'] = $this->currentTime() + $this->GetLimitValue($item_proto, $i);
					
						if($item_shop['time']>0)//shop
							$item['socket0'] = $this->currentTime() + $item_shop['time']*60;
					}
					else
					{
						if($add_type=='item')
							$item['socket0'] = $this->currentTime() + 60*60*24*7;
				
						if($item_shop['time']>0)//shop
							$item['socket0'] = $this->currentTime() + $item_shop['time']*60;
					}
					
					if($add_type=='item')
						$item['socket1'] = $this->GetSocket($vnum, 1) + 1;
				}
				else if('LIMIT_REAL_TIME_FIRST_USE' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
				{
					if($this->GetLimitValue($item_proto, $i))
					{
						if($add_type=='item')
							$item['socket0'] = $this->currentTime() + $this->GetLimitValue($item_proto, $i);
					
						if($item_shop['time']>0)//shop
							$item['socket0'] = $item_shop['time']*60;
					}
					else
					{
						if($add_type=='item')
							$item['socket0'] = $this->currentTime() + 60*60*24*7;
				
						if($item_shop['time']>0)//shop
							$item['socket0'] = $this->currentTime() + $item_shop['time']*60;
					}
					
					if($add_type=='item')
						$item['socket1'] = $this->GetSocket($vnum, 1) + 1;
				}
				else if('LIMIT_TIMER_BASED_ON_WEAR' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
				{
					$duration = $this->GetSocket($vnum, 0);
					if(0 == $duration)
						$duration = $this->GetLimitValue($item_proto, $i);

					if(0 == $duration)
						$duration = 60 * 60 * 10;
					
					if($add_type=='item')
						$item['socket0'] = $duration;
					
					if($item_shop['time']>0)//shop
						$item['socket0'] = $item_shop['time']*60;
				}
			}
			
			if($add_type=='item' && $itemType == 'ITEM_BLEND')
			{
				$jsondataBlend = file_get_contents('include/db/blend.json');
				$jsondataBlend = json_decode($jsondataBlend, true);
				
				foreach($jsondataBlend as $blend_info)
					if($blend_info['item_vnum'] == $vnum)
					{
						if($vnum == 51002)
						{
							$apply_type = array_search($this->server_item['c_aApplyTypeNames'][$blend_info['apply_type']], $this->server_item['EApplyTypes']);
							$apply_value = $blend_info['apply_value'][$this->FN_ECS_random_index()];
							$apply_duration	= $blend_info['apply_duration'][$this->FN_ECS_random_index()];
						}
						else
						{
							$apply_type = array_search($this->server_item['c_aApplyTypeNames'][$blend_info['apply_type']], $this->server_item['EApplyTypes']);
							$apply_value = $blend_info['apply_value'][$this->FN_random_index()];
							$apply_duration	= $blend_info['apply_duration'][$this->FN_random_index()];
						}
						$item['socket0']=$apply_type;
						$item['socket1']=$apply_value;
						$item['socket2']=$apply_duration;
					}
			}

			if($add_type=='item' && $item_proto['attu_addon']!=0)
			{
				$addon = $this->GetAddon($item_proto['attu_addon']);
				
				$apply = array_search('APPLY_NORMAL_HIT_DAMAGE_BONUS', $this->server_item['EApplyTypes']);
				$item['attrtype'.count($attr_used)]=$apply;
				$item['attrvalue'.count($attr_used)]=$addon[0];
				$attr_used[]=$apply;
				
				$apply = array_search('APPLY_SKILL_DAMAGE_BONUS', $this->server_item['EApplyTypes']);
				$item['attrtype'.count($attr_used)]=$apply;
				$item['attrvalue'.count($attr_used)]=$addon[1];
				$attr_used[]=$apply;
			}

			if($add_type=='item' && in_array($this->GetType($item_proto), array('ITEM_WEAPON', 'ITEM_ARMOR', 'ITEM_COSTUME')))
			{
				$iRarePct = $item_proto['magic_pct'];

				if(rand(1, 100) <= $iRarePct)
				{
					//item->AlterToMagicItem();
					if($this->GetType($item_proto) == 'ITEM_WEAPON')
					{
						$iSecondPct = 20;
						$iThirdPct = 5;
					}
					else if($this->GetType($item_proto) == 'ITEM_ARMOR' || $this->GetType($item_proto) == 'ITEM_COSTUME')
					{
						$iSecondPct = 10;
						$iThirdPct = 1;
					}

					$attr = $this->GetAttribute($this->server_item['aiItemMagicAttributePercentHigh'], $item_proto['item_type'], $item_proto['sub_type'], $attr_used);
					if($attr[0] && $attr[1])
					{
						$item['attrtype'.count($attr_used)]=$attr[0];
						$item['attrvalue'.count($attr_used)]=$attr[1];
						
						$attr_used[]=$attr[0];
					}

					if(rand(1, 100) <= $iSecondPct)
					{
						$attr = $this->GetAttribute($this->server_item['aiItemMagicAttributePercentLow'], $item_proto['item_type'], $item_proto['sub_type'], $attr_used);
						if($attr[0] && $attr[1])
						{
							$item['attrtype'.count($attr_used)]=$attr[0];
							$item['attrvalue'.count($attr_used)]=$attr[1];
							
							$attr_used[]=$attr[0];
						}
					}

					if(rand(1, 100) <= $iSecondPct)
					{
						$attr = $this->GetAttribute($this->server_item['aiItemMagicAttributePercentLow'], $item_proto['item_type'], $item_proto['sub_type'], $attr_used);
						if($attr[0] && $attr[1])
						{
							$item['attrtype'.count($attr_used)]=$attr[0];
							$item['attrvalue'.count($attr_used)]=$attr[1];
							
							$attr_used[]=$attr[0];
						}
					}
				}
			}
		}
		
		if($vnum == 50300 || $vnum == $this->server_item['unique_item']['ITEM_SKILLFORGET_VNUM'])
		{
			if($item_shop['book_type']=='RANDOM_ALL_CHARS')
			{
				if($wolfman_character)
					$skillVnum = rand(0, count($this->server_item['SkillList'])-1);
				else
					$skillVnum = rand(0, count($this->server_item['SkillList'])-7);
				$skillVnum = $this->server_item['SkillList'][$skillVnum];
			} else if($item_shop['book_type']=='FIX')
				$skillVnum = $item_shop['book'];
			else {
				$random_skills = ['JOB_WARRIOR' => array_slice($this->server_item['SkillList'], 0, 12),
									'JOB_WARRIOR1' => array_slice($this->server_item['SkillList'], 0, 6),
									'JOB_WARRIOR2' => array_slice($this->server_item['SkillList'], 6, 6),
									'JOB_ASSASSIN' => array_slice($this->server_item['SkillList'], 12, 12),
									'JOB_ASSASSIN1' => array_slice($this->server_item['SkillList'], 12, 6),
									'JOB_ASSASSIN2' => array_slice($this->server_item['SkillList'], 18, 6),
									'JOB_SURA' => array_slice($this->server_item['SkillList'], 24, 12),
									'JOB_SURA1' => array_slice($this->server_item['SkillList'], 24, 6),
									'JOB_SURA2' => array_slice($this->server_item['SkillList'], 30, 6),
									'JOB_SHAMAN' => array_slice($this->server_item['SkillList'], 36, 12),
									'JOB_SHAMAN1' => array_slice($this->server_item['SkillList'], 36, 6),
									'JOB_SHAMAN2' => array_slice($this->server_item['SkillList'], 42, 6),
									'JOB_WOLFMAN' => array_slice($this->server_item['SkillList'], 48, 6)];
				$skillVnum = rand(0, count($random_skills[$item_shop['book_type']])-1);
				$skillVnum = $random_skills[$item_shop['book_type']][$skillVnum];
			}
			
			$item['socket0'] = $skillVnum;
		}
		else if($vnum == $this->server_item['unique_item']['ITEM_SKILLFORGET2_VNUM'])
		{
			$dwSkillVnum = rand(112, 119);
			$item['socket0'] = $dwSkillVnum;
		}
		
		if($item_shop['type']==1)
		{
			$shop_bonuses = false;
			for($i=0;$i<=6;$i++)
				if($item_shop['attrtype'.$i]>0)
					$shop_bonuses = true;
			
			if($shop_bonuses)
				for($i=0;$i<=6;$i++)
				{
					$item['attrtype'.$i] = $item_shop['attrtype'.$i];
					$item['attrvalue'.$i] = $item_shop['attrvalue'.$i];
				}
		} else if($item_shop['type']==2)
		{
			$i = 0;
			foreach($selected_bonuses as $bonus=>$value)
			{
				$item['attrtype'.$i] = $bonus;
				$item['attrvalue'.$i] = $value;
				$i++;
			}
		}
		
		if($add_type=='item_award')
		{
			$item_columns = $this->getItemAwardColumns();
			
			foreach($item as $key => $value)
				if(!in_array($key, $item_columns))
					unset($item[$key]);
				
			if($this->db->insert("item_award", $item))
				return true;
		} else {
			$item_columns = $this->getItemColumns();
			
			foreach($item as $key => $value)
				if(!in_array($key, $item_columns))
					unset($item[$key]);
			if($this->db->insert("item", $item))
				return true;
		}
		return false;
		//print_r($item);
	}
	
	public function getAdminAvatar($id)
	{
		$admin = $this->db->get("player", ["job", "name"], [
										"account_id" => $id,
										"name[~]" => "[",
										'LIMIT' => 1
									]);
		
		if($admin!=null)
			return array($admin['job'], $admin['name']);
		
		return array(0, $this->account->getAccountData('login', $id));
	}
	
	public function checkItemColumnSockets()
	{
		$i=0;
		$columns = $this->db->query("DESCRIBE item")->fetchAll(PDO::FETCH_COLUMN);
		
		foreach($columns as $column)
			if(strncmp($column, "socket", 6) === 0 && strlen($column)==7)
				$i++;
		
		return $i;
	}
	
	public function getItemBonusesAddon($item_proto, $vnum) {
		$bonuses = [];
		
		if($item_proto)
			for($i=0;$i<=2;$i++)
				if($item_proto['addon_type'.$i].$i!='' && $item_proto['addon_type'.$i].$i!='APPLY_NONE' && $item_proto['addon_value'.$i]>0)
					$bonuses[] = array(array_search($item_proto['addon_type'.$i], $this->server_item['EApplyTypes']), $item_proto['addon_value'.$i]);
		
		return $bonuses;
	}
	
	public function getItemBonuses($item_proto, $vnum, $max=0) {//unused
		$bonuses = [];
		
		if($item_proto)
		{
			if($item_proto['attu_addon']!=0)
			{
				$bonuses[] = array(array_search('APPLY_NORMAL_HIT_DAMAGE_BONUS', $this->server_item['EApplyTypes']), 0);
				$bonuses[] = array(array_search('APPLY_SKILL_DAMAGE_BONUS', $this->server_item['EApplyTypes']), 0);
			} else {
				for($i=0;$i<=2;$i++)
					if($item_proto['addon_type'.$i].$i!='' && $item_proto['addon_type'.$i].$i!='APPLY_NONE' && $item_proto['addon_value'.$i]>0)
						$bonuses[] = array(array_search($item_proto['addon_type'.$i], $this->server_item['EApplyTypes']), $item_proto['addon_value'.$i]);
			}
			
			if(in_array($this->GetType($item_proto), array('ITEM_WEAPON', 'ITEM_ARMOR', 'ITEM_COSTUME')))
			{
				$iAttributeSet = $this->GetAttributeSetIndex($item_proto['item_type'], $item_proto['sub_type']);
				$TItemAttrTable = $this->GetTItemAttrTable();
				
				if($iAttributeSet < 0)
					return $bonuses;
				
				for ($i = 0; $i < count($TItemAttrTable); ++$i)
				{
					$r = $TItemAttrTable[$i];

					if($r['bMaxLevelBySet'][$iAttributeSet] && !in_array($r['dwApplyIndex'], $bonuses))
					{
						$bonuses[]=array($i, 0);
						if($max && count($bonuses)>=$max)
							return $bonuses;
					}
				}
			}
		}
		
		return $bonuses;
	}
	
	public function getItemProtoDuration($item_proto)
	{
		$itemType = $this->GetType($item_proto);
		
		if($itemType == 'ITEM_UNIQUE')
			return $this->GetValue($item_proto, 0)/60;
		
		for ($i=0 ; $i < $this->server_item['EItemMisc']['ITEM_LIMIT_MAX_NUM']; $i++)
		{
			if('LIMIT_REAL_TIME' == 'LIMIT_'.$this->GetLimitType($item_proto, $i) || 'LIMIT_REAL_TIME_FIRST_USE' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
			{
				if($this->GetLimitValue($item_proto, $i))
					return $this->GetLimitValue($item_proto, $i)/60;
				else
					return 60*24*7;
			}
			else if('LIMIT_TIMER_BASED_ON_WEAR' == 'LIMIT_'.$this->GetLimitType($item_proto, $i))
			{
				$duration = $this->GetSocket($vnum, 0);
				if(0 == $duration)
					$duration = $this->GetLimitValue($item_proto, $i);

				if(0 == $duration)
					$duration = 60 * 60 * 10;
				
				return $duration/60;
			}
		}
		return 0;
	}
	
	public function getPlayerAccount($name)
	{
		return $this->db->get("player", "account_id", ["name[~]" => $name]);
	}
	
	public function getPlayerID($name)
	{
		return $this->db->get("player", "id", ["name[~]" => $name]);
	}
}