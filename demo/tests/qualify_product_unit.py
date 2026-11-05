"""Native candidate-test fixture isolation; no product feature or deployment claim."""
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'demo'))
from factory.product_unit import ProductUnitRunner

PROBE='''
import java.net.*;
public class UnitFixture {
  public static void main(String[] args) throws Exception {
    var env=System.getenv();
    for (String key: new String[]{"OPENCODE_API_KEY","GH_API_KEY","GH_BUILD_KEY","GH_RELEASE_KEY"})
      if (env.containsKey(key)) throw new IllegalStateException("HOST_CREDENTIAL_VISIBLE");
    if (!"aeion_fixture_admin".equals(env.get("AEION_TEST_POSTGRES_USERNAME")))
      throw new IllegalStateException("OWNED_ADMIN_MISSING");
    if (env.getOrDefault("AEION_TEST_POSTGRES_PASSWORD", "").length()<32)
      throw new IllegalStateException("FIXTURE_PASSWORD_MISSING");
    if (!"jdbc:postgresql://127.0.0.1:5432/aeion_factory_test".equals(env.get("AEION_TEST_POSTGRES_JDBC_URL")))
      throw new IllegalStateException("UNEXPECTED_DATABASE_ENDPOINT");
    try (var socket=new Socket()) { socket.connect(new InetSocketAddress("127.0.0.1",5432),2000); }
    try (var socket=new Socket()) {
      socket.connect(new InetSocketAddress("1.1.1.1",443),500);
      throw new IllegalStateException("EXTERNAL_EGRESS_AVAILABLE");
    } catch (java.io.IOException expected) { }
  }
}
'''


def main():
    runner=ProductUnitRunner(ROOT)
    with tempfile.TemporaryDirectory(prefix='aeion-unit-fixture-') as folder:
        source=Path(folder)/'UnitFixture.java';source.write_text(PROBE)
        result=runner(['java',str(source)],cwd=folder,timeout=60)
        assert result.returncode==0,'Native candidate-test fixture probe failed'
        assert result.qualification['postgres']['teardown_confirmed'] is True
    proof={'status':'passed','kind':'owned_candidate_unit_fixture','real_model_requests':0,
        'own_administrator_available':True,'host_credentials_absent':True,
        'owned_loopback_available':True,'external_egress_denied':True,'teardown_confirmed':True,
        'product_delivery_claimed':False}
    folder=Path(tempfile.mkdtemp(prefix='aeion-product-unit-proof-',dir='/private/tmp'))
    (folder/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'evidence':str(folder/'proof.json'),**proof}))


if __name__=='__main__':main()
