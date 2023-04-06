from flask import Flask, redirect, url_for, request, jsonify
import json
app = Flask(__name__)



topologies = [
   {'id': 1, 'name': 'topologie1'},
   {'id': 2, 'name': 'topologie2'},
   {'id': 3, 'name': 'topologie3'}
]

nexttopologyid = 4

@app.route('/topologies',methods = ['GET'])
def get_topologies():
   return jsonify(topologies)

@app.route('/topologies/<string:name>', methods=['GET'])
def get_topology_by_name(name: str):
   topology = get_topology(name)
   if topology is None:
      return jsonify({'error': 'Topology does not exist'}, 404)
   return jsonify(topology)

def get_topology(name):
   return next((t for t in topologies if t['name'] == name), None)

def topology_is_valid(topology):
   for key in topology.keys():
      if key != 'name':
         return False
   return True



@app.route('/topologies', methods=['POST'])
def add_topology():
   global nexttopologyid
   topology = json.loads(request.data)
   if not topology_is_valid(topology):
      return jsonify({'error': 'Invalid topology properties'}), 400


   topology['id'] = nexttopologyid
   nexttopologyid += 1
   topologies.append(topology)

   return '', 201, {'location': f'/topologies/{topology["name"]}'}



@app.route('/topologies/<string:name>', methods=['PUT'])
def update_topology(name: str):
   topology = get_topology(name)
   if topology is None:
      return jsonify({'error': 'Topology does not exist'}), 404

   updated_topology = json.loads(request.data)
   if not topology_is_valid(updated_topology):
      return jsonify({'error': 'Invalid topology properties'}), 400

   topology.update(updated_topology)

   return jsonify(topology)



@app.route('/topologies/<string:name>', methods=['DELETE'])
def delete_topology(name: str):
   global topologies
   topology = get_topology(name)
   if topology is None:
      return jsonify({'error': 'Topology does not exist'}), 404

   topologies = [t for t in topologies if t['name'] != name]
   return jsonify(topology), 200

if __name__ == '__main__':
   app.run(debug = True)