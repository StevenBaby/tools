#!/usr/bin/python3
# coding=utf8
'''
Description: Add information in python file
Author: Steven Kang
Datetime: 2018-05-29 11:35:45
'''

import datetime
import sublime_plugin


class InformationCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        contents = """'''\n"""\
            """Description: ${{1:Description...}}\n"""\
            """Author: ${{2:Steven Kang}}\n"""\
            """Datetime: {datetime}\n"""\
            """'''\n""".format(
                datetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        self.view.run_command("insert_snippet", {"contents": contents})
