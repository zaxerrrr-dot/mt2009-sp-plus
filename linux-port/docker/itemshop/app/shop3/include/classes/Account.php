<?php
use Medoo\Medoo;
class Account {

	private $db = NULL, $player = NULL;

	public function __construct($db) {
		$this->db = $db; 
	}

	public function setPlayerDB($db)
	{
		$this->player = $db; 
	}

	public function getAccountData($column, $id)
	{
		return $this->db->get("account", $column, [
			"id" => $id
		]);
	}

	public function getAccountDataByLogin($column, $login)
	{
		return $this->db->get("account", $column, [
			"login" => $login
		]);
	}
	
	private function getHashPassword($password)
	{
		$hash = "*".sha1(sha1($password, true));
		return strtoupper($hash);
	}
	
	private function check_account_column($name)
	{
		$columns = $this->db->query("DESCRIBE account")->fetchAll(PDO::FETCH_COLUMN);
		
		if(in_array($name, $columns))
			return true;
		else return false;
	}
	
	private function check_availDt($id)
	{
		$availDt = $this->getAccountData('availDt', $id);
		
		if($availDt != "0000-00-00 00:00:00")
		{	
			$date1 = new DateTime("now");
			$date2 = new DateTime($availDt);
			if($date1 < $date2)
				return true;
		}
		
		return false;
	}

	private function securityPassword($password)
	{
		return md5($password[10].$password[7].$password[3].$password[12].$password[24].$password[17].$password[26].$password[29].$password[18].$password[6]);
	}
	
	public function doLogin($login, $password, $admin=false)
	{
		global $shop_url;
		$password = $this->getHashPassword($password);
		
		if ($this->db->has("account", [
			"AND" => [
				"login" => $login,
				"password" => $password
			]
		]))
		{
			$user = $this->db->get("account", [
				"id",
				"status",
				"password"
			], [
				"AND" => [
					"login" => $login,
					"password" => $password
				]
			]);
			if($user['status']=='OK')
			{
				if($this->check_account_column('availDt') && $this->check_availDt($user['id']))
					return 2;
				
				$_SESSION['id'] = $user['id'];
				$_SESSION['password'] = $this->securityPassword($user['password']);
				$_SESSION['fingerprint'] = md5($_SERVER['HTTP_USER_AGENT'] . 'x' . $_SERVER['REMOTE_ADDR']);
				
				if(false)	// MT2009_PLUS_ITEMSHOP_V3_V1: no web_admin column, no admin panel
				{
					$adminAvatar = $this->player->getAdminAvatar($_SESSION['id']);
					$_SESSION['admin'] = $adminAvatar[0];
					$_SESSION['welcome'] = $adminAvatar[1];
				}
				if($admin)
					header("Location: ".$shop_url.'admin');
				else
					header("Location: ".$shop_url);
				die();
			} else return 2;
		}
		else
			return 1;
	}
	
	public function AutoLoginShop($PID,$SAS){
		global $database, $game_ishop_key, $shop_url;
		
		if(!is_numeric($PID))
			return false;
		
		$account_id = $this->player->getPlayerData('account_id', $PID);
		
		$hash_generate = md5($PID.$account_id.$game_ishop_key);
		if(is_numeric($PID) && $SAS && $hash_generate == $SAS){
			$user = $this->db->get("account", [
				"id",
				"status",
				"password"
			], ["id" => $account_id]);

			if($user['status']=='OK')
			{
				if($this->check_account_column('availDt') && $this->check_availDt($user['id']))
					return false;
				
				$_SESSION['id'] = $user['id'];
				$_SESSION['game'] = true;
				// MT2009_PLUS_ITEMSHOP_V3_V2: the character of the link - the shop shows what it can wear
				// (header.php) and names it at the purchase.
				$_SESSION['pid'] = (int)$PID;
				$_SESSION['password'] = $this->securityPassword($user['password']);
				$_SESSION['fingerprint'] = md5($_SERVER['HTTP_USER_AGENT'] . 'x' . $_SERVER['REMOTE_ADDR']);
				
				header("Location: ".$shop_url);
				die();
			} else return false;

			return false;
		} else
			return false;
	}
	
	public function doLogout()
	{
		session_destroy();
		unset($_SESSION['id']);
		unset($_SESSION['password']);
		unset($_SESSION['fingerprint']);
		if(isset($_SESSION['admin']))
			unset($_SESSION['admin']);
		if(isset($_SESSION['game']))
			unset($_SESSION['game']);
		return true;
	}
	
	public function checkPassword($id, $password)
	{
		$password = $this->getHashPassword($password);
		
		if($password==$this->getAccountData('password', $id))
			return true;
		return false;
	}
	
	public function is_loggedin()
	{
		if(isset($_SESSION['id']))
			return true;
		else return false;
	}
	
	public function is_in_game()
	{
		if(isset($_SESSION['game']))
			return true;
		else return false;
	}
	
	public function is_loggedin_admin()
	{
		if(isset($_SESSION['admin']))
			return true;
		else return false;
	}
	
	// MT2009_PLUS_ITEMSHOP_V3_V1: the package's "coins" / "jcoins" are our Smocze Monety (account.cash,
	// "SM") and Smocze Znaki (account.cash_mark, "SZ") - the same balances the old shop, the Kolo Losu and
	// the in-game shop spend. Taken in one UPDATE that only passes with enough on the account (the
	// package read, subtracted and read again, and two purchases at once could both pass).
	// MT2009_PLUS_SZ_UNIFIED_V1: one Smocze Znaki balance everywhere - account.cash_mark, the one the game
	// (in-game shop) and the panel show (owner, 24.10.2026); mileage was moved into it once.
	public static function currencyColumn($type)
	{
		return $type==1 ? 'cash' : 'cash_mark';
	}

	public function getCoins($type, $id)
	{
		return (int)$this->getAccountData(self::currencyColumn($type), $id);
	}

	public function payCoins($type, $coins)
	{
		$coins = (int)$coins;
		if($coins==0)
			return true;
		if($coins<0)
			return false;

		$column = self::currencyColumn($type);
		$sth = $this->db->pdo->prepare("UPDATE account SET `".$column."` = `".$column."` - ? WHERE id = ? AND `".$column."` >= ?");
		$sth->execute([$coins, (int)$_SESSION['id'], $coins]);
		return $sth->rowCount()==1;
	}

	public function addCoinsByLogin($type, $coins, $login)
	{
		return $this->db->update("account", [self::currencyColumn($type)."[+]" => (int)$coins], ["login" => $login]);
	}

	public function addCoinsByID($type, $coins, $login)
	{
		return $this->db->update("account", [self::currencyColumn($type)."[+]" => (int)$coins], ["id" => $login]);
	}
	
	public function addBuff($item_shop, $account)
	{
		global $server_item;
		
		if(!isset($server_item['buff'][$item_shop['vnum']][0]))
			return false;
		
		$account_column = $server_item['buff'][$item_shop['vnum']][0];
		$time = $item_shop['time'];//minutes
		
		$sth = $this->db->pdo->prepare("SELECT (".$account_column."-NOW()) as time FROM account WHERE id = ?");
		
		$sth->bindParam(1, $account, PDO::PARAM_STR);
		$sth->execute();
			
		$result=$sth->fetch(PDO::FETCH_ASSOC);
		
		if(isset($result['time']))
		{
			if($result['time']<0)
			{
				$this->db->update("account", [$account_column => Medoo::raw('NOW() + INTERVAL '.$time.' MINUTE')], ["id" => $account]);
				return true;
			}
			else {
				$this->db->update("account", [$account_column => Medoo::raw($account_column.' + INTERVAL '.$time.' MINUTE')], ["id" => $account]);
				return true;
			}
		}
		return false;
	}

	public function getMultipleAccounts($accounts) {
		$result = array();
		
		$names = $this->db->select("account", ["id", "login"], ["id" => $accounts]);
		
		foreach($names as $name)
			$result[$name['id']] = $name['login'];
		
		foreach($accounts as $account)
			if(!isset($result[$account]))
				$result[$account] = 'ID: '.$account;
		
		return $result;
	}
	
	public function getAccountsLike($searchString) {
		$string = '%'.strtolower($searchString).'%';
		
		$sth = $this->db->pdo->prepare("SELECT id FROM account WHERE LOWER(login) LIKE ?");
		$sth->bindParam(1, $string, PDO::PARAM_STR);
		$sth->execute();
		$result = $sth->fetchAll();
		
		if($result && is_array($result) && count($result))
			return array_column($result, 'id');
		
		return [0];
	}
	
	public function checkStatus($account) {
		$status = $this->getAccountData('status', $account);
		
		if(!$status || $status!='OK')
			return false;
		return true;
	}
}