#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i4b: direct Player Progression implementation."""
from __future__ import annotations

import ast
import base64
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.12i4b"
OLD_ADD = base64.b64decode("ZGVmIGFkZF9leHAodXNlcl9pZDogaW50LCBhbW91bnQpOgogICAgbGVnYWN5ID0gX2xlZ2FjeV9mdW5jdGlvbigiYWRkX2V4cCIpCiAgICBpZiBsZWdhY3k6CiAgICAgICAgcmV0dXJuIGxlZ2FjeSh1c2VyX2lkLCBhbW91bnQpCgogICAgcm93ID0gX2ZldGNob25lKCJTRUxFQ1QgZXhwIEZST00gdXNlcnMgV0hFUkUgdXNlcl9pZD0/IiwgKHVzZXJfaWQsKSkKICAgIGN1cnJlbnQgPSBpbnQoX3Jvd19nZXQocm93LCAiZXhwIiwgMCwgMCkgb3IgMCkKICAgIG5ld192YWx1ZSA9IGN1cnJlbnQgKyBpbnQoYW1vdW50KQogICAgX2V4ZWN1dGVfY29tbWl0KCJVUERBVEUgdXNlcnMgU0VUIGV4cD0/IFdIRVJFIHVzZXJfaWQ9PyIsIChuZXdfdmFsdWUsIHVzZXJfaWQpKQogICAgcmV0dXJuIHsiZXhwIjogbmV3X3ZhbHVlLCAibGV2ZWwiOiBnZXRfcGxheWVyX2xldmVsKHVzZXJfaWQpLCAibGV2ZWxfdXBzIjogMH0K").decode("utf-8")
NEW_ADD = base64.b64decode("ZGVmIGFkZF9leHAodXNlcl9pZDogaW50LCBhbW91bnQpOgogICAgIiIiQWRkIEVYUCBhbmQgcHJlc2VydmUgdGhlIGhpc3RvcmljYWwgZGIucHkgcHJvZ3Jlc3Npb24gY29udHJhY3QuIiIiCiAgICBkYiA9IF9kYl9tb2R1bGUoKQoKICAgIHJvdyA9IF9mZXRjaG9uZSgKICAgICAgICAiU0VMRUNUIGxldmVsLCBleHAgRlJPTSB1c2VycyBXSEVSRSB1c2VyX2lkPT8iLAogICAgICAgICh1c2VyX2lkLCksCiAgICApCiAgICBpZiBub3Qgcm93OgogICAgICAgIHJldHVybiBOb25lCgogICAgbGV2ZWwgPSBpbnQoX3Jvd19nZXQocm93LCAibGV2ZWwiLCAwLCAxKSBvciAxKQogICAgZXhwID0gaW50KF9yb3dfZ2V0KHJvdywgImV4cCIsIDEsIDApIG9yIDApCiAgICBleHAgKz0gaW50KGFtb3VudCkKICAgIGxldmVsX3VwcyA9IDAKCiAgICB3aGlsZSBleHAgPj0gZGIuZ2V0X2V4cF90b19uZXh0X2xldmVsKGxldmVsKToKICAgICAgICBleHAgLT0gZGIuZ2V0X2V4cF90b19uZXh0X2xldmVsKGxldmVsKQogICAgICAgIGxldmVsICs9IDEKICAgICAgICBsZXZlbF91cHMgKz0gMQoKICAgICAgICBkYi5jdXJzb3IuZXhlY3V0ZSgKICAgICAgICAgICAgIiIiCiAgICAgICAgICAgIFVQREFURSB1c2VycwogICAgICAgICAgICBTRVQKICAgICAgICAgICAgICAgIHN0ciA9IHN0ciArIDEsCiAgICAgICAgICAgICAgICBkZXggPSBkZXggKyAxLAogICAgICAgICAgICAgICAgaW50ZWxsaWdlbmNlID0gaW50ZWxsaWdlbmNlICsgMSwKICAgICAgICAgICAgICAgIHdpcyA9IHdpcyArIDEsCiAgICAgICAgICAgICAgICBzdGEgPSBzdGEgKyAxCiAgICAgICAgICAgIFdIRVJFIHVzZXJfaWQ9PwogICAgICAgICAgICAiIiIsCiAgICAgICAgICAgICh1c2VyX2lkLCksCiAgICAgICAgKQoKICAgIGRiLmN1cnNvci5leGVjdXRlKAogICAgICAgICJVUERBVEUgdXNlcnMgU0VUIGxldmVsPT8sIGV4cD0/IFdIRVJFIHVzZXJfaWQ9PyIsCiAgICAgICAgKGxldmVsLCBleHAsIHVzZXJfaWQpLAogICAgKQogICAgZGIuY29ubi5jb21taXQoKQoKICAgIG1heF9ocCA9IGdldF9tYXhfaHAodXNlcl9pZCkKICAgIGRiLmN1cnNvci5leGVjdXRlKAogICAgICAgICJVUERBVEUgdXNlcnMgU0VUIG1heF9ocD0/IFdIRVJFIHVzZXJfaWQ9PyIsCiAgICAgICAgKG1heF9ocCwgdXNlcl9pZCksCiAgICApCiAgICBkYi5jb25uLmNvbW1pdCgpCgogICAgcmV0dXJuIHsKICAgICAgICAibGV2ZWwiOiBsZXZlbCwKICAgICAgICAiZXhwIjogZXhwLAogICAgICAgICJleHBfdG9fbmV4dCI6IGRiLmdldF9leHBfdG9fbmV4dF9sZXZlbChsZXZlbCksCiAgICAgICAgImxldmVsX3VwcyI6IGxldmVsX3VwcywKICAgIH0K").decode("utf-8")
OLD_PROGRESS = base64.b64decode("ZGVmIGdldF91c2VyX3Byb2dyZXNzKHVzZXJfaWQ6IGludCk6CiAgICBsZWdhY3kgPSBfbGVnYWN5X2Z1bmN0aW9uKCJnZXRfdXNlcl9wcm9ncmVzcyIpCiAgICBpZiBsZWdhY3k6CiAgICAgICAgcmV0dXJuIGxlZ2FjeSh1c2VyX2lkKQoKICAgIHJvdyA9IF9mZXRjaG9uZSgKICAgICAgICAiIiIKICAgICAgICBTRUxFQ1QgbGV2ZWwsIGV4cCwgZ29sZCwga2lsbHMKICAgICAgICBGUk9NIHVzZXJzCiAgICAgICAgV0hFUkUgdXNlcl9pZD0/CiAgICAgICAgIiIiLAogICAgICAgICh1c2VyX2lkLCksCiAgICApCgogICAgaWYgbm90IHJvdzoKICAgICAgICByZXR1cm4gTm9uZQoKICAgIHJldHVybiB7CiAgICAgICAgImxldmVsIjogaW50KF9yb3dfZ2V0KHJvdywgImxldmVsIiwgMCwgMSkgb3IgMSksCiAgICAgICAgImV4cCI6IGludChfcm93X2dldChyb3csICJleHAiLCAxLCAwKSBvciAwKSwKICAgICAgICAiZ29sZCI6IGZsb2F0KF9yb3dfZ2V0KHJvdywgImdvbGQiLCAyLCAwKSBvciAwKSwKICAgICAgICAia2lsbHMiOiBpbnQoX3Jvd19nZXQocm93LCAia2lsbHMiLCAzLCAwKSBvciAwKSwKICAgIH0K").decode("utf-8")
NEW_PROGRESS = base64.b64decode("ZGVmIGdldF91c2VyX3Byb2dyZXNzKHVzZXJfaWQ6IGludCk6CiAgICAiIiJSZXR1cm4gdGhlIGhpc3RvcmljYWwgc2l4LWtleSBwbGF5ZXIgcHJvZ3Jlc3Npb24gZGljdGlvbmFyeS4iIiIKICAgIGRiID0gX2RiX21vZHVsZSgpCiAgICByb3cgPSBfZmV0Y2hvbmUoCiAgICAgICAgIiIiCiAgICAgICAgU0VMRUNUIGxldmVsLCBleHAsIGdvbGQsIGtpbGxzLCBkYWlseV9odW50cwogICAgICAgIEZST00gdXNlcnMKICAgICAgICBXSEVSRSB1c2VyX2lkPT8KICAgICAgICAiIiIsCiAgICAgICAgKHVzZXJfaWQsKSwKICAgICkKICAgIGlmIG5vdCByb3c6CiAgICAgICAgcmV0dXJuIE5vbmUKCiAgICBsZXZlbCA9IGludChfcm93X2dldChyb3csICJsZXZlbCIsIDAsIDEpIG9yIDEpCiAgICByZXR1cm4gewogICAgICAgICJsZXZlbCI6IGxldmVsLAogICAgICAgICJleHAiOiBpbnQoX3Jvd19nZXQocm93LCAiZXhwIiwgMSwgMCkgb3IgMCksCiAgICAgICAgImV4cF90b19uZXh0IjogZGIuZ2V0X2V4cF90b19uZXh0X2xldmVsKGxldmVsKSwKICAgICAgICAiZ29sZCI6IF9yb3dfZ2V0KHJvdywgImdvbGQiLCAyLCAwKSwKICAgICAgICAia2lsbHMiOiBfcm93X2dldChyb3csICJraWxscyIsIDMsIDApLAogICAgICAgICJkYWlseV9odW50cyI6IGludChfcm93X2dldChyb3csICJkYWlseV9odW50cyIsIDQsIDApIG9yIDApLAogICAgfQo=").decode("utf-8")
TEST_SOURCE = base64.b64decode("IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiJST00gOS4wLjEyaTRiOiBpc29sYXRlZCBQbGF5ZXIgUHJvZ3Jlc3Npb24gZXF1aXZhbGVuY2UgdGVzdC4iIiIKZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwoKaW1wb3J0IHN5cwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKClJPT1QgPSBQYXRoKF9fZmlsZV9fKS5yZXNvbHZlKCkucGFyZW50c1sxXQppZiBzdHIoUk9PVCkgbm90IGluIHN5cy5wYXRoOgogICAgc3lzLnBhdGguaW5zZXJ0KDAsIHN0cihST09UKSkKCmltcG9ydCBkYgpmcm9tIHN5c3RlbXMgaW1wb3J0IHBsYXllcl9zeXN0ZW0KClRFU1RfVVNFUl9JRCA9IC05MDEyMDQwMgpMRUdBQ1lfQUREID0gIl9sZWdhY3lfYWRkX2V4cF9iZWZvcmVfcGxheWVyX3N5c3RlbV92MSIKTEVHQUNZX1BST0dSRVNTID0gIl9sZWdhY3lfZ2V0X3VzZXJfcHJvZ3Jlc3NfYmVmb3JlX3BsYXllcl9zeXN0ZW1fdjEiCgoKZGVmIGZhaWwobWVzc2FnZSk6CiAgICBwcmludChmIltGQUlMXSB7bWVzc2FnZX0iKQogICAgcmFpc2UgU3lzdGVtRXhpdCgxKQoKCmRlZiBjbGVhbnVwKCk6CiAgICAjIFJlbW92ZSBvbmx5IHRoZSBpc29sYXRlZCBuZWdhdGl2ZSB0ZXN0IGZpeHR1cmUgYW5kIGl0cyByZWxhdGVkIHJvd3MuCiAgICBmb3IgdGFibGUgaW4gKCJlcXVpcG1lbnRfc2xvdHMiLCAiaW52ZW50b3J5IiwgInVzZXJfYWN0aXZlX2NvbnRyYWN0cyIsICJ1c2VyX2RhaWx5X3F1ZXN0cyIpOgogICAgICAgIHRyeToKICAgICAgICAgICAgZGIuY3Vyc29yLmV4ZWN1dGUoZiJERUxFVEUgRlJPTSB7dGFibGV9IFdIRVJFIHVzZXJfaWQ9PyIsIChURVNUX1VTRVJfSUQsKSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgICAgICBwYXNzCiAgICBkYi5jdXJzb3IuZXhlY3V0ZSgiREVMRVRFIEZST00gdXNlcnMgV0hFUkUgdXNlcl9pZD0/IiwgKFRFU1RfVVNFUl9JRCwpKQogICAgZGIuY29ubi5jb21taXQoKQoKCmRlZiBpbnNlcnRfZml4dHVyZShsZXZlbCwgZXhwLCBzdGF0cz0xMCk6CiAgICBjbGVhbnVwKCkKICAgIGRiLmN1cnNvci5leGVjdXRlKAogICAgICAgICIiIgogICAgICAgIElOU0VSVCBJTlRPIHVzZXJzICgKICAgICAgICAgICAgdXNlcl9pZCwgaHAsIG1heF9ocCwgbGV2ZWwsIGV4cCwgZ29sZCwga2lsbHMsIGJhZ19zbG90cywKICAgICAgICAgICAgY3VycmVudF9sb2NhdGlvbiwgc3RyLCBkZXgsIGludGVsbGlnZW5jZSwgd2lzLCBzdGEsIGRhaWx5X2h1bnRzCiAgICAgICAgKSBWQUxVRVMgKD8sID8sID8sID8sID8sID8sID8sID8sID8sID8sID8sID8sID8sID8sID8pCiAgICAgICAgIiIiLAogICAgICAgICgKICAgICAgICAgICAgVEVTVF9VU0VSX0lELCAxNzAsIDE3MCwgaW50KGxldmVsKSwgaW50KGV4cCksIDEyLjUsIDcsIDQwLAogICAgICAgICAgICAic3RhcnRfcGF0aCIsIGludChzdGF0cyksIGludChzdGF0cyksIGludChzdGF0cyksIGludChzdGF0cyksCiAgICAgICAgICAgIGludChzdGF0cyksIDMsCiAgICAgICAgKSwKICAgICkKICAgIGRiLmNvbm4uY29tbWl0KCkKCgpkZWYgc25hcHNob3QoKToKICAgIHJldHVybiBkYi5jdXJzb3IuZXhlY3V0ZSgKICAgICAgICAiIiIKICAgICAgICBTRUxFQ1QgbGV2ZWwsIGV4cCwgc3RyLCBkZXgsIGludGVsbGlnZW5jZSwgd2lzLCBzdGEsIG1heF9ocAogICAgICAgIEZST00gdXNlcnMgV0hFUkUgdXNlcl9pZD0/CiAgICAgICAgIiIiLAogICAgICAgIChURVNUX1VTRVJfSUQsKSwKICAgICkuZmV0Y2hvbmUoKQoKCmRlZiBydW5fcGF0aChmdW5jdGlvbiwgbGV2ZWwsIGV4cCwgYW1vdW50KToKICAgIGluc2VydF9maXh0dXJlKGxldmVsLCBleHApCiAgICByZXN1bHQgPSBmdW5jdGlvbihURVNUX1VTRVJfSUQsIGFtb3VudCkKICAgIHN0YXRlID0gc25hcHNob3QoKQogICAgcHJvZ3Jlc3MgPSBwbGF5ZXJfc3lzdGVtLmdldF91c2VyX3Byb2dyZXNzKFRFU1RfVVNFUl9JRCkKICAgIHJldHVybiByZXN1bHQsIHR1cGxlKHN0YXRlKSBpZiBzdGF0ZSBpcyBub3QgTm9uZSBlbHNlIE5vbmUsIHByb2dyZXNzCgoKZGVmIG1haW4oKToKICAgIGxlZ2FjeV9hZGQgPSBnZXRhdHRyKGRiLCBMRUdBQ1lfQURELCBOb25lKQogICAgbGVnYWN5X3Byb2dyZXNzID0gZ2V0YXR0cihkYiwgTEVHQUNZX1BST0dSRVNTLCBOb25lKQogICAgaWYgbm90IGNhbGxhYmxlKGxlZ2FjeV9hZGQpIG9yIG5vdCBjYWxsYWJsZShsZWdhY3lfcHJvZ3Jlc3MpOgogICAgICAgIGZhaWwoImxlZ2FjeSBwcm9ncmVzc2lvbiBjYXB0dXJlcyBhcmUgbWlzc2luZyIpCgogICAgY2FzZXMgPSBbXQogICAgdGhyZXNob2xkXzEgPSBpbnQoZGIuZ2V0X2V4cF90b19uZXh0X2xldmVsKDEpKQogICAgdGhyZXNob2xkXzIgPSBpbnQoZGIuZ2V0X2V4cF90b19uZXh0X2xldmVsKDIpKQogICAgY2FzZXMuYXBwZW5kKCgibm9fbGV2ZWxfdXAiLCAxLCAwLCBtYXgoMSwgdGhyZXNob2xkXzEgLy8gMikpKQogICAgY2FzZXMuYXBwZW5kKCgib25lX2xldmVsX3VwIiwgMSwgbWF4KDAsIHRocmVzaG9sZF8xIC0gMyksIDUpKQogICAgY2FzZXMuYXBwZW5kKCgibXVsdGlwbGVfbGV2ZWxfdXBzIiwgMSwgMCwgdGhyZXNob2xkXzEgKyB0aHJlc2hvbGRfMiArIDExKSkKCiAgICBjb21wYXJpc29ucyA9IDAKICAgIHRyeToKICAgICAgICBmb3IgbGFiZWwsIGxldmVsLCBleHAsIGFtb3VudCBpbiBjYXNlczoKICAgICAgICAgICAgbGVnYWN5ID0gcnVuX3BhdGgobGVnYWN5X2FkZCwgbGV2ZWwsIGV4cCwgYW1vdW50KQogICAgICAgICAgICBkaXJlY3QgPSBydW5fcGF0aChwbGF5ZXJfc3lzdGVtLmFkZF9leHAsIGxldmVsLCBleHAsIGFtb3VudCkKICAgICAgICAgICAgY29tcGFyaXNvbnMgKz0gMQogICAgICAgICAgICBpZiBsZWdhY3kgIT0gZGlyZWN0OgogICAgICAgICAgICAgICAgZmFpbChmIntsYWJlbH0gbWlzbWF0Y2g6IGxlZ2FjeT17bGVnYWN5IXJ9LCBkaXJlY3Q9e2RpcmVjdCFyfSIpCgogICAgICAgICMgUmVhZC1vbmx5IGdldF91c2VyX3Byb2dyZXNzIGNvbXBhcmlzb24gb24gYWxsIHJlYWwgdXNlcnMuCiAgICAgICAgcm93cyA9IGRiLmN1cnNvci5leGVjdXRlKAogICAgICAgICAgICAiU0VMRUNUIHVzZXJfaWQgRlJPTSB1c2VycyBXSEVSRSB1c2VyX2lkPj0wIE9SREVSIEJZIHVzZXJfaWQiCiAgICAgICAgKS5mZXRjaGFsbCgpCiAgICAgICAgcHJvZ3Jlc3NfY29tcGFyaXNvbnMgPSAwCiAgICAgICAgZm9yICh1c2VyX2lkLCkgaW4gcm93czoKICAgICAgICAgICAgcHVibGljX3ZhbHVlID0gZGIuZ2V0X3VzZXJfcHJvZ3Jlc3ModXNlcl9pZCkKICAgICAgICAgICAgZGlyZWN0X3ZhbHVlID0gcGxheWVyX3N5c3RlbS5nZXRfdXNlcl9wcm9ncmVzcyh1c2VyX2lkKQogICAgICAgICAgICBsZWdhY3lfdmFsdWUgPSBsZWdhY3lfcHJvZ3Jlc3ModXNlcl9pZCkKICAgICAgICAgICAgcHJvZ3Jlc3NfY29tcGFyaXNvbnMgKz0gMQogICAgICAgICAgICBpZiBub3QgKHB1YmxpY192YWx1ZSA9PSBkaXJlY3RfdmFsdWUgPT0gbGVnYWN5X3ZhbHVlKToKICAgICAgICAgICAgICAgIGZhaWwoZiJnZXRfdXNlcl9wcm9ncmVzcyBtaXNtYXRjaCBmb3IgdXNlciB7dXNlcl9pZH0iKQoKICAgICAgICBtaXNzaW5nID0gLTk4NzY1NDMyMQogICAgICAgIGlmIG5vdCAoCiAgICAgICAgICAgIGRiLmdldF91c2VyX3Byb2dyZXNzKG1pc3NpbmcpCiAgICAgICAgICAgID09IHBsYXllcl9zeXN0ZW0uZ2V0X3VzZXJfcHJvZ3Jlc3MobWlzc2luZykKICAgICAgICAgICAgPT0gbGVnYWN5X3Byb2dyZXNzKG1pc3NpbmcpCiAgICAgICAgKToKICAgICAgICAgICAgZmFpbCgibWlzc2luZy11c2VyIHByb2dyZXNzIGJlaGF2aW9yIG1pc21hdGNoIikKICAgIGZpbmFsbHk6CiAgICAgICAgY2xlYW51cCgpCgogICAgbGVmdG92ZXIgPSBkYi5jdXJzb3IuZXhlY3V0ZSgKICAgICAgICAiU0VMRUNUIENPVU5UKCopIEZST00gdXNlcnMgV0hFUkUgdXNlcl9pZD0/IiwgKFRFU1RfVVNFUl9JRCwpCiAgICApLmZldGNob25lKClbMF0KICAgIGlmIGludChsZWZ0b3ZlciBvciAwKSAhPSAwOgogICAgICAgIGZhaWwoImlzb2xhdGVkIHRlc3QgdXNlciB3YXMgbm90IHJlbW92ZWQiKQoKICAgIHByaW50KCJbT0tdIHBsYXllciBwcm9ncmVzc2lvbiBkaXJlY3QgaW1wbGVtZW50YXRpb24iKQogICAgcHJpbnQoZiItIGFkZF9leHAgZXF1aXZhbGVuY2UgY2FzZXM6IHtjb21wYXJpc29uc30iKQogICAgcHJpbnQoZiItIGdldF91c2VyX3Byb2dyZXNzIGNvbXBhcmlzb25zOiB7cHJvZ3Jlc3NfY29tcGFyaXNvbnN9IikKICAgIHByaW50KCItIG1pc21hdGNoZXM6IDAiKQogICAgcHJpbnQoIi0gbGV2ZWwtdXAgc3RhdCBpbmNyZW1lbnRzOiBPSyIpCiAgICBwcmludCgiLSBtYXggSFAgc3luY2hyb25pemF0aW9uOiBPSyIpCiAgICBwcmludCgiLSBtaXNzaW5nLXVzZXIgY29udHJhY3Q6IE9LIikKICAgIHByaW50KCItIGlzb2xhdGVkIHRlc3QgdXNlciBjbGVhbnVwOiBPSyIpCiAgICBwcmludCgiLSByZWFsIHVzZXIgbXV0YXRpb25zOiAwIikKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbWFpbigpCg==").decode("utf-8")


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    script = Path(__file__).resolve()
    for candidate in (script.parent.parent, Path.cwd(), Path.cwd().parent):
        candidate = candidate.resolve()
        if (candidate / "db.py").is_file() and (candidate / "systems" / "player_system.py").is_file():
            return candidate
    fail("Не знайдено корінь ROM.")


def main():
    root = find_root()
    player_path = root / "systems" / "player_system.py"
    test_path = root / "tools" / "smoke_test_player_progression_direct.py"
    source = player_path.read_text(encoding="utf-8-sig")

    already_applied = (
        NEW_ADD in source and NEW_PROGRESS in source
        and OLD_ADD not in source and OLD_PROGRESS not in source
    )
    if already_applied:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірку.")
        if not test_path.is_file():
            test_path.write_text(TEST_SOURCE, encoding="utf-8")
        result = subprocess.run([sys.executable, str(test_path)], cwd=root)
        raise SystemExit(result.returncode)

    if source.count(OLD_ADD) != 1:
        fail(f"Legacy-блок add_exp знайдено {source.count(OLD_ADD)} разів замість 1.")
    if source.count(OLD_PROGRESS) != 1:
        fail(f"Legacy-блок get_user_progress знайдено {source.count(OLD_PROGRESS)} разів замість 1.")

    updated = source.replace(OLD_ADD, NEW_ADD, 1)
    updated = updated.replace(OLD_PROGRESS, NEW_PROGRESS, 1)
    try:
        ast.parse(updated, filename=str(player_path))
    except SyntaxError as exc:
        fail(f"AST-перевірка не пройдена: {exc}")

    for function_name in ("add_exp", "get_user_progress"):
        tree = ast.parse(updated)
        nodes = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        ]
        if len(nodes) != 1:
            fail(f"systems/player_system.py: {function_name} definitions={len(nodes)}.")
        segment = ast.get_source_segment(updated, nodes[0]) or ""
        if "_legacy_function" in segment:
            fail(f"{function_name} все ще залежить від _legacy_function.")

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    player_backup = backup_dir / f"systems_player_system.py_{PATCH_ID}_direct_progression_{stamp}.bak"
    shutil.copy2(player_path, player_backup)
    test_backup = None
    if test_path.exists():
        test_backup = backup_dir / f"tools_smoke_test_player_progression_direct.py_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    temp_path = player_path.with_name(".player_system.i4b.tmp")
    try:
        temp_path.write_text(updated, encoding="utf-8")
        os.replace(temp_path, player_path)
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(player_path), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        result = subprocess.run([sys.executable, str(test_path)], cwd=root)
        if result.returncode != 0:
            raise RuntimeError(f"progression test exit code {result.returncode}")
    except Exception as exc:
        shutil.copy2(player_backup, player_path)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        if temp_path.exists():
            temp_path.unlink()
        fail(f"Перевірка не пройдена; файли відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ add_exp реалізовано безпосередньо в systems/player_system.py.")
    print("✅ get_user_progress реалізовано безпосередньо в systems/player_system.py.")
    print("✅ Два legacy captures у db.py збережено для контрольного порівняння.")
    print("✅ Ізольований тестовий користувач видалений після перевірки.")
    print("Резервні копії:")
    print(f"   {player_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./systems/player_system.py")
    print("   python ./tools/smoke_test_player_progression_direct.py")
    print("   python ./tools/smoke_test_player_progression_legacy_audit.py")
    print("   python ./tools/smoke_test_player_contracts.py")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
