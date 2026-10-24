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
			"login[~]" => $login
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
				"login[~]" => $login,
				"password" => $password
			]
		]))
		{
			$user = $this->db->get("account", [
				"id",
				"status",
				"password",
				"web_admin"
			], [
				"AND" => [
					"login[~]" => $login,
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
				
				if($admin && $user['web_admin']>=9)
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
				"password",
				"web_admin"
			], ["id" => $account_id]);

			if($user['status']=='OK')
			{
				if($this->check_account_column('availDt') && $this->check_availDt($user['id']))
					return false;
				
				$_SESSION['id'] = $user['id'];
				$_SESSION['game'] = true;
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
	
	public function payCoins($type, $coins)
	{
		if($coins==0)
			return true;
		
		$amount_coins = $this->getAccountData('coins', $_SESSION['id']);
		$amount_jcoins = $this->getAccountData('jcoins', $_SESSION['id']);
		
		if($type==1)
		{
			if($coins>$amount_coins)
				return false;
			$data = $this->db->update("account", ["coins[-]" => $coins], ["id" => $_SESSION['id']]);
			
			if(!$data->rowCount())
				return false;
			
			$amount_coins_after = $this->getAccountData('coins', $_SESSION['id']);
			if($amount_coins_after != $amount_coins - $coins)
			{
				if($amount_coins_after<0)
					$this->db->update("account", ["coins" => 0], ["id" => $_SESSION['id']]);
				return false;
			}
		}
		else
		{
			if($coins>$amount_jcoins)
				return false;
			$data = $this->db->update("account", ["jcoins[-]" => $coins], ["id" => $_SESSION['id']]);
			
			if(!$data->rowCount())
				return false;
			
			$amount_jcoins_after = $this->getAccountData('jcoins', $_SESSION['id']);
			if($amount_jcoins_after != $amount_jcoins - $coins)
			{
				if($amount_jcoins_after<0)
					$this->db->update("account", ["jcoins" => 0], ["id" => $_SESSION['id']]);
				return false;
			}
		}
		
		if($data->rowCount())
			return true;
		else return false;
	}
	
	public function addCoinsByLogin($type, $coins, $login)
	{
		if($type==1)
			return $this->db->update("account", ["coins[+]" => $coins], ["login" => $login]);
		else
			return $this->db->update("account", ["jcoins[+]" => $coins], ["login" => $login]);
	}
	
	public function addCoinsByID($type, $coins, $login)
	{
		if($type==1)
			return $this->db->update("account", ["coins[+]" => $coins], ["id" => $login]);
		else
			return $this->db->update("account", ["jcoins[+]" => $coins], ["id" => $login]);
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