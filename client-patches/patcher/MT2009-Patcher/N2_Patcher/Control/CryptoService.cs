using N2_Patcher.Model;
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace N2_Patcher.Control
{
	internal class CryptoService
	{
		public CryptoService()
		{
		}

		private static byte[] Decrypt(byte[] cipherData, byte[] Key, byte[] IV)
		{
			MemoryStream memoryStream = new MemoryStream();
			Rijndael key = Rijndael.Create();
			key.Key = Key;
			key.IV = IV;
			CryptoStream cryptoStream = new CryptoStream(memoryStream, key.CreateDecryptor(), CryptoStreamMode.Write);
			cryptoStream.Write(cipherData, 0, (int)cipherData.Length);
			cryptoStream.Close();
			return memoryStream.ToArray();
		}

		public static string DecryptString(string cipherText)
		{
			byte[] numArray = Convert.FromBase64String(cipherText);
			PasswordDeriveBytes passwordDeriveByte = new PasswordDeriveBytes(Config.getPrivateKey(), new byte[] { 73, 118, 97, 110, 32, 77, 101, 100, 118, 101, 100, 101, 118 });
			byte[] numArray1 = CryptoService.Decrypt(numArray, passwordDeriveByte.GetBytes(32), passwordDeriveByte.GetBytes(16));
			return Encoding.Unicode.GetString(numArray1);
		}
	}
}