import lxml.etree, lxml.objectify
import math
import bisect
import re

def svgPathTokenize(data):
	''' Loops through the path data and splits it into commands and data for those commands '''
	tokens = []
	current_token = {"command": "", "data": ""}
	for i in data:
		if re.match("[a-zA-Z]", i):
			if current_token['command'] != "": 
				current_token['data'] = current_token['data'].strip()
				tokens.append(dict(current_token))
			current_token['command'] = i
			current_token['data'] = ""
		else:
			if (i == "-"): current_token['data'] += " "
			current_token['data'] += i

	current_token['data'] = current_token['data'].strip()
	tokens.append(current_token)
	return tokens

def svgPathParse(tokenizedData):
	output_line = []
	c_x = 0 #current X and Y pos of cursor
	c_y = 0
	s_x = 0 #starting X and Y pos - used for z command
	s_y = 0
	first_command_flag = True
	bez_prev_x = False
	bez_prev_x = False
	#start with some validation
	if tokenizedData[0]['command'] not in ['M', 'm']:
		print("Parse error: Path must begin with M or m")
		return []
	
	for t in tokenizedData:
		#Lower-case SVG Path commands are relative commands.
		#However, if they are the first command in the path, they are treated as absolute.
		relative = 1 if (t['command'].islower() and first_command_flag == False) else 0
		coords = re.split("[ ,]", t['data'])
		if t['command'] in ['M', 'm']: #move to
			if len(coords) % 2 != 0 :
				print("Parse error: M command with coordinates not multiple of 2")
				return []
			elif len(coords) == 2:
				c_x = float(coords[0]) + (c_x * relative)
				c_y = float(coords[1]) + (c_y * relative)
			elif len(coords) > 2:
				c_x = float(coords[0]) + (c_x * relative)
				c_y = float(coords[1]) + (c_y * relative)
				for c in range(2, len(coords), 2):
					output_line.append({"type": "line",
										"x1": c_x,
										"y1": c_y,
										"x2": float(coords[c]),
										"y2": float(coords[c+1])})
					c_x = float(coords[c])
					c_y = float(coords[c+1])

			if first_command_flag == True:
				s_x = float(coords[0]) 
				s_y = float(coords[1])
				
		elif t['command'] in ['L', 'l']: #line to
			if len(coords) % 2 != 0 :
				print("Parse error: L command with coordinates not multiple of 2")
				return []
			else:
				for c in range(0, len(coords), 2):
					output_line.append({"type": "line",
										"x1": c_x,
										"y1": c_y,
										"x2": float(coords[c]) + (c_x * relative),
										"y2": float(coords[c+1]) + (c_y * relative)})
					c_x = float(coords[c]) + (c_x * relative)
					c_y = float(coords[c+1]) + (c_y * relative)
		elif t['command'] in ['H', 'h']:
			
			for c in range(0, len(coords)):
				output_line.append({"type": "line",
									"x1": c_x,
									"y1": c_y,
									"x2": float(coords[c]) + (c_x * relative),
									"y2": c_y})
				c_x = float(coords[c]) + (c_x * relative)
		elif t['command'] in ['V', 'v']:
			for c in range(0, len(coords)):
				output_line.append({"type": "line",
									"x1": c_x,
									"y1": c_y,
									"x2": c_x,
									"y2": float(coords[c]) + (c_y * relative)})
				c_x = float(coords[c]) + (c_x * relative)
		elif t['command'] in ['C', 'c']:
			if len(coords) % 6 != 0 :
				print("Parse error: C command with coordinates not multiple of 6")
				return []
			else:
				for c in range(0, len(coords), 6):

					output_line.append({"type": "bezier",
										"x1": c_x,
										"y1": c_y,
										"cx1": float(coords[c]) + (c_x * relative), 
										"cy1": float(coords[c+1]) + (c_x * relative), 
										"cx2": float(coords[c+2]) + (c_x * relative), 
										"cy2": float(coords[c+3]) + (c_x * relative), 
										"x2" : float(coords[c+4]) + (c_x * relative), 
										"y2" : float(coords[c+5]) + (c_x * relative)})
					bez_prev_x = (2 * (float(coords[c+4]) + c_x * relative)) - (float(coords[c+2]) + (c_x * relative))
					bez_prev_y = (2 * (float(coords[c+5]) + c_y * relative)) - (float(coords[c+3]) + (c_y * relative))

					c_x = float(coords[c+4]) + (c_x * relative)
					c_y = float(coords[c+5]) + (c_y * relative)
					
					
		elif t['command'] in ['S', 's']:
			if len(coords) % 4 != 0 :
				print("Parse error: S command with coordinates not multiple of 4")
				return []
			else:
				if bez_prev_x == False or bez_prev_y == False:
					bez_prev_x = c_x
					bez_prev_y = c_y

				for c in range(0, len(coords), 4):
					output_line.append({"type": "bezier",
										"x1": c_x,
										"y1": c_y,
										"cx1": bez_prev_x, 
										"cy1": bez_prev_y, 
										"cx2": float(coords[c+0]) + (c_x * relative), 
										"cy2": float(coords[c+1]) + (c_x * relative), 
										"x2" : float(coords[c+2]) + (c_x * relative), 
										"y2" : float(coords[c+3]) + (c_x * relative)})
					bez_prev_x = (2 * (float(coords[c+2]) + c_x * relative)) - (float(coords[c+0]) + (c_x * relative))
					bez_prev_y = (2 * (float(coords[c+3]) + c_y * relative)) - (float(coords[c+1]) + (c_y * relative))
					
					c_x = float(coords[c+2]) + (c_x * relative)
					c_y = float(coords[c+3]) + (c_y * relative)
					
		elif t['command'] == "z":
			if t['data'] != "":
				print("Parse error: z command with data")
				return []
			else:
				output_line.append({"type": "line",
									"x1": c_x,
									"y1": c_y,
									"x2": s_x,
									"y2": s_y})
				c_x = s_x
				c_y = s_y
		else:
			print(f"Parse error: unrecognized command {t['command']}")
			return []

		first_command_flag = False

		if t['command'] not in ['C', 'c', 'S', 's']:
			bez_prev_x = False
			bez_prev_y = False
	return output_line

def bezierToLineSegments(x1, y1, cx1, cy1, cx2, cy2, x2, y2):
	'''Splits a bezier curve into equal-length line segments. 
	There is no closed-form equation for this and the exact mathematical way involves integrals and is slow.
	But we don't need to be perfect so we just step through the curve and define a point every time we go
	past the desired distance. Much faster and gives "good enough" accuracy. '''
	min_length = 10
	output_points = []
	opx = x1
	opy = y1
	t = 0
	if (math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2)) < math.pow(min_length, 2)):
		output_points.append({
						  "x1"   : x1,
						  "x2"   : x2,
						  "y1"   : y1,
						  "y2"   : y2})	
		return output_points

	while (t < 1):
		t += 0.001
		px = (math.pow(1 - t, 3) * x1) + (3 * math.pow(1 - t,2) * t * cx1) + (3 * math.pow(t,2) * (1- t) * cx2) + (math.pow(t, 3) * x2)
		py = (math.pow(1 - t, 3) * y1) + (3 * math.pow(1 - t,2) * t * cy1) + (3 * math.pow(t,2) * (1- t) * cy2) + (math.pow(t, 3) * y2)
		if (math.sqrt(math.pow(px - opx, 2) + math.pow(py - opy, 2)) > math.pow(min_length, 2)):
			output_points.append({"x1"   : opx,
								  "x2"   : px,
								  "y1"   : opy,
								  "y2"   : py})
			opx = px
			opy = py
	output_points.append({"x1"   : output_points[-1]['x2'],
	   					  "x2"   : x2,
						  "y1"   : output_points[-1]['y2'],
						  "y2"   : y2})
	return output_points
		
class gcodeParser:
	def __init__(self):
		self.parse_logic = {"circle": self.svgCircle,
						"line"  : self.svgLine,
						"path"  : self.svgPath
		}
		self.pen_diameter = 1 #all units are mm
		self.lsd = 10 #line segment distance - defines the distance line segments take in bezier curves
		self.gcode_lift_pen = "G1 Z0 F1000\n"
		self.gcode_lower_pen = "G1 Z20 F1000\n"
		self.gcode_drawspeed = 10000
		self.gcode_travelspeed = 10000
		self.scale_factor = 0.5
	def svgCircle(self, tag):
		return []
		#return tag.attrib
	
	def svgPath(self, tag):
		#First: tokenize
		
		tok = svgPathTokenize(tag.attrib['d'])
		seg_list = svgPathParse(tok)
		return seg_list

	def svgLine(self, tag):
		try:
			data = [{"type" : "line",
					"x1"   : float(tag.attrib['x1']),
					"x2"   : float(tag.attrib['x2']),
					"y1"   : float(tag.attrib['y1']),
					"y2"   : float(tag.attrib['y2'])}]
		except:
			self.log("Parse error, ignoring:", lxml.etree.tostring(tag))
			return {"type" : "fail"}
		return data

	def log(self, error, data="", level='error'):
		if level=='error':
			print(error, data)
		elif level=='info':
			print(error, data)


	def lineSegmentsToGcode(self, segments):
		gcode = ""
		c_x = 0
		c_y = 0
		#TODO: Implement something to rearrange the draw commands for better draw speed
		for tags in segments:
			for s in tags:
				
				if s['x1'] != c_x and s['y1'] != c_y:
					print (f"Lifting pen; old coords {c_x:.2f}, {c_y:.2f}; new coords {s['x1']:.2f}, {s['y1']:.2f}")
					gcode += self.gcode_lift_pen
					gcode += f"G1 X{(s['x1'] * self.scale_factor):.2f} Y{(s['y1'] * self.scale_factor):.2f} F{self.gcode_travelspeed}\n"
					gcode += self.gcode_lower_pen
				if s['type'] == 'line':
					gcode += f"G1 X{(s['x2']* self.scale_factor):.2f} Y{(s['y2'] * self.scale_factor):.2f} F{self.gcode_drawspeed}\n"
				elif s['type'] == 'bezier':
					t_points = bezierToLineSegments(s['x1'], s['y1'], s['cx1'], s['cy1'], s['cx2'], s['cy2'],s['x2'], s['y2'])
					for l in t_points:
						gcode += f"G1 X{(l['x2'] * self.scale_factor):.2f} Y{(l['y2'] * self.scale_factor):.2f} F{self.gcode_drawspeed}\n"

				c_x = s['x2'] * self.scale_factor
				c_y = s['y2'] * self.scale_factor
		return gcode

	def parseSVG(self, root):
		data = []
		
		for child in root:
			t = re.sub(r'^{[^}]*}', "", child.tag)
			if t in self.parse_logic.keys():
				print(t)
				parsed_value = self.parse_logic[t](child)
				if isinstance(parsed_value, str):
					print(parsed_value)
					return []
				data.append(parsed_value)
				
			elif t == "g":
				data += self.parseSVG(child)
			else:
				self.log("Parse error, ignoring:", child.tag)
		return data
		
		
		


root = lxml.etree.parse('7food_network_logo.svg').getroot()
p = gcodeParser()
gcode = p.lineSegmentsToGcode(p.parseSVG(root))

f = open("7food_network_logo2.gcode", "w+")
f.write(gcode)
f.close()

