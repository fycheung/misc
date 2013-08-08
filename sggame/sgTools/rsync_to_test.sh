#!/bin/bash

rsync "-e ssh -p22" -avuHS /data1/sg_game/trunk/sgLib/* 183.60.41.107:/data1/sg_game/trunk/sgLib
rsync "-e ssh -p22" -avuHS /data1/sg_game/trunk/sgMod/* 183.60.41.107:/data1/sg_game/trunk/sgMod
rsync "-e ssh -p22" -avuHS /data1/sg_game/trunk/sgServer/* 183.60.41.107:/data1/sg_game/trunk/sgServer
