#!/usr/local/bin/python3

# .
# ├── run.py     -- このPythonスクリプト
# ├── listfiles  -- ペレトロンで取った元のリストデータを入れるフォルダ
# ├── bin        -- C言語のソースファイルや実行ファイルを入れるフォルダ
# ├── anampa     -- anampaで処理したファイルを入れるフォルダ
# ├── au_ph      -- gatempaでgateをかけたAuの波高スペクトルのフォルダ
# ├── op_ph      -- gatempaでgateをかけたブランクの波高スペクトルのフォルダ
# └── te_ph      -- gatempaでgateをかけたTeの波高スペクトルのフォルダ
#

# こういうスクリプトを書くときのコツは、
# 解析の変更に対する、スクリプトの変更を最小限に抑えるように書くこと。
# できるだけデータを出力してグラフ化し、物理的に不自然な点がないか確認すること。


import subprocess
import glob
import numpy as np


def cmd(command):
    subprocess.call(command, shell=True)

# すべてのリストファイルに対してanampaを実行する
# anampa.cをコンパイルした実行ファイルの名前はanampaであると想定
# $ gcc ANAMPA.C -o anampa
#
for listfile in glob.glob("listfiles/*.lst"):
    outname = listfile.replace("listfiles", "anampa")
    cmd("bin/anampa %s %s" % (listfile, outname))


# gateのチャンネルを指定する
# バックグラウンドはサンプルによって変更する
fore_gates = [(380, 393),
              (393, 420),
              (420, 458),
              (458, 500),
              (500, 540)]
back_gates = (800, 1000)


#
# ここからはAuの処理のみを書いています。
# ほかのサンプルも同様にできます。
#




# Auについて、gatempaを実行する
# gatempa.cをコンパイルした実行ファイルの名前がgatempaであると想定
# $ gcc GATEMPA.C -o gatempa
#
for au_list in glob.glob("anampa/au*"):
    # foreground
    gate_number = 1
    for gate in fore_gates:
        outname = au_list.replace("anampa", "au_ph").replace("lst", "")
        outname +=  "_gate%d.ph" % gate_number
        low, high = gate
        cmd("bin/gatempa %s 1 %d %d %s" % (au_list, low, high, outname))
        gate_number += 1
    # background
    outname = au_list.replace("anampa", "au_ph").replace("lst", "")
    outname += "_bg.ph"
    low, high = back_gates
    cmd("bin/gatempa %s 1 %d %d %s" % (au_list, low, high, outname))


# foregroundのgateごとの和を出す
for gate in len(fore_gates):
    # すべて値が0のベクトルを準備
    sum_ph = np.zeros(2048)
    for ph_file in glob.glob("au_ph/*_gate%d.ph" % gate+1):
        # すべてのRunを足していく
        sum_ph += np.loadtxt(ph_file)
    # 足した結果を保存する
    np.savetxt("au_ph/sum_au_gate%d.ph" % gate+1, sum_ph)

# backgroundのgateごとの和を出す
sum_ph = np.zeros(2048)
for ph_file in glob.glob("au_ph/*_bg.ph"):
    sum_ph += np.loadtxt(ph_file)
    np.savetxt("au_ph/sum_au_bg.ph" % sum_ph)


# 正味の波高スペクトルを求める。
back_ch_width = back_gates[1] - back_gates[0] + 1
gate_number = 1
for gate in fore_gates:
    fore_ch_width = gate[1] - gate[0] + 1
    fore_spectrum = np.loadtxt("au_ph/sum_au_%s.ph" % gate_number)
    back_spectrum = np.loadtxt("au_ph/sum_au_bg.ph")
    # signalを計算
    signal_spectrum = fore_spectrum - back_spectrum * fore_ch_width/back_ch_width
    # errを計算
    err = np.sqrt(fore_spectrum**2 + (back_spectrum*fore_ch_width/back_ch_width)**2)
    # チャンネル
    ch = np.arrange(2048)+1
    # 保存する行列
    out = np.vstack([ch, signal_spectrum, err]).T
    # 保存
    np.savetxt("signal_au_gate%d.ph" % gate_number, out)
    gate_number += 1
