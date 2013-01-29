#!/usr/local/bin/python -O
# -*- coding: utf8 -*-

import main

if __name__ == "__main__":
        if __debug__:
                import cProfile, time
                time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                cProfile.run("main.run()", "../log/prof-%s" %time_str)
        else:
                main.run()