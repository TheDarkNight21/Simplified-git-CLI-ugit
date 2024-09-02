# Create a canvas widget in the root window
set c [canvas .canvas -width 400 -height 300]
pack $c -expand true -fill both

# Now, add the canvas drawing commands
$c create polygon 87.5 5.333 23.5 5.333 23.5 53.333 95.5 53.333 95.5 13.333 -fill white -width 1 -outline black -tags {1node0x12560ab70}
$c create line 87.5 5.333 87.5 13.333 -fill black -tags {1node0x12560ab70}
$c create line 95.5 13.333 87.5 13.333 -fill black -tags {1node0x12560ab70}
$c create text 59.5 29.3 -text {HEAD} -fill black -font {"Times" 14} -tags {0node0x12560ab70}

# Next element
$c create polygon 113.667 101.333 5.333 101.333 5.333 149.333 113.667 149.333 -fill lightgrey -width 1 -outline black -tags {1node0x12560adc0}
$c create text 59.5 125.3 -text {3bc2c9b84e} -fill black -font {"Times" 14} -tags {0node0x12560adc0}

# Line connecting HEAD to the next commit
$c create line 59.5 53.738 59.5 63.458 59.5 75.031 59.5 85.952 -fill black -width 1 -smooth bezier -tags {1edge0x12560aeb0}
$c create polygon 64.167 85.843 59.5 99.176 54.833 85.843 -fill black -width 1 -outline black -tags {1edge0x12560aeb0}

# Next commit
$c create polygon 113.167 197.333 5.833 197.333 5.833 245.333 113.167 245.333 -fill lightgrey -width 1 -outline black -tags {1node0x12560b0c0}
$c create text 59.5 221.3 -text {dd1f2111a7} -fill black -font {"Times" 14} -tags {0node0x12560b0c0}

# Line connecting the commits
$c create line 59.5 149.738 59.5 159.458 59.5 171.031 59.5 181.952 -fill black -width 1 -smooth bezier -tags {1edge0x12560b170}
$c create polygon 64.167 181.843 59.5 195.176 54.833 181.843 -fill black -width 1 -outline black -tags {1edge0x12560b170}