# zaif_calc_tax
zaif_calc_taxは仮想通貨取引所[zaif](https://zaif.jp)の取引履歴と含み益、損益計算をしてくれるプログラムです。出力は現在csvファイルに対応しています。

## Demo

## Requirement
[zaifapi](https://github.com/techbureau/zaifapi)

## Usage　使い方
１．pipコマンドを実行、モジュールをダウンロード
```
pip install　zaifapi
```
2．リポジトリからダウンロード

3.pythonコンパイラ上で開く

4.input.csvにてzaifから発行したapiキーとシークレットキーを入力

5.zaif以外からの入金やクレジットカード購入などがある場合はadd.csvに記入例を参考に入力。
参考[日付からタイムスタンプに変換(プログラムで自動変換するようにする予定です)](http://url-c.com/tc/)

6.zaif.pyを実行
エラーが出る場合は入力漏れがある可能性があります。zaif以外で買ったものを送金していたりzaifの簡単売買やクレジットカード購入をしている場合はその情報もinput.csvに入力してくださ。
7.output.csvに出力されています
## Licence

[MIT](https://github.com/tcnksm/tool/blob/master/LICENCE)

## Author

[watarishiki](https://github.com/watarishiki)
