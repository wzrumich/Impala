# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import pytest
import tempfile
import socket
import pexpect
import os

from tests.common.custom_cluster_test_suite import CustomClusterTestSuite
from tests.common.impala_service import ImpaladService
from tests.shell.util import ImpalaShell
# Follow tests/shell/test_shell_interactive.py naming.
from shell.impala_shell import ImpalaShell as ImpalaShellClass

SHELL_CMD = "%s/bin/impala-shell.sh" % os.environ['IMPALA_HOME']
NUM_QUERIES = 'impala-server.num-queries'

class TestShellInteractiveReconnect(CustomClusterTestSuite):
  """ Check if interactive shell is using the current DB after reconnecting """
  @classmethod
  def get_workload(cls):
    return 'functional-query'

  @pytest.mark.execute_serially
  def test_manual_reconnect(self):
    p = ImpalaShell()
    p.send_cmd("USE functional")
    p.send_cmd("CONNECT")
    p.send_cmd("SHOW TABLES")

    result = p.get_result()
    assert "alltypesaggmultifilesnopart" in result.stdout

  @pytest.mark.execute_serially
  def test_auto_reconnect(self):
    impalad = ImpaladService(socket.getfqdn())
    start_num_queries = impalad.get_metric_value(NUM_QUERIES)

    p = ImpalaShell()
    p.send_cmd("USE functional")

    # wait for the USE command to finish
    impalad.wait_for_metric_value(NUM_QUERIES, start_num_queries + 1)
    assert impalad.wait_for_num_in_flight_queries(0)

    self._start_impala_cluster([])

    p.send_cmd("SHOW TABLES")
    result = p.get_result()
    assert "alltypesaggmultifilesnopart" in result.stdout

  @pytest.mark.execute_serially
  def test_auto_reconnect_after_impalad_died(self):
    """Test reconnect after restarting the remote impalad without using connect;"""
    # Use pexpect instead of ImpalaShell() since after using get_result() in ImpalaShell()
    # to check Disconnect, send_cmd() will no longer have any effect so we can not check
    # reconnect.
    impalad = ImpaladService(socket.getfqdn())
    start_num_queries = impalad.get_metric_value(NUM_QUERIES)

    proc = pexpect.spawn(' '.join([SHELL_CMD, "-i localhost:21000"]))
    proc.expect("21000] default>")
    proc.sendline("use tpch;")

    # wait for the USE command to finish
    impalad.wait_for_metric_value(NUM_QUERIES, start_num_queries + 1)
    assert impalad.wait_for_num_in_flight_queries(0)

    # Disconnect
    self.cluster.impalads[0].kill()
    proc.sendline("show tables;")
    # Search from [1:] since the square brackets "[]" are special characters in regex
    proc.expect(ImpalaShellClass.DISCONNECTED_PROMPT[1:])
    # Restarting Impalad
    self.cluster.impalads[0].start()
    # Check reconnect
    proc.sendline("show tables;")
    proc.expect("nation")
    proc.expect("21000] tpch>")
