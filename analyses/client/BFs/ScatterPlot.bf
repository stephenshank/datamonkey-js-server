/*---------------------------------------------------------
output a postscript header; set page size
---------------------------------------------------------*/

function _HYPSPageHeader (_width,_height,_doc_title)
{
	
	_res_string = "";
	_res_string * 64;
	_res_string * "%!\n";
	_res_string * ("%% PS file " + _doc_title);
	GetString (_hpv,HYPHY_VERSION,0);
	GetString (_cdt,TIME_STAMP,0);
	_res_string * ("\n%% Generated by HYPHY v" + _hpv + " on GMT " + _cdt);
	_res_string * ("\n<< /PageSize ["+_width+" "+_height+ "] >> setpagedevice");
	_res_string * 0;
	return _res_string;
}

/*---------------------------------------------------------
set a font (face and size)
---------------------------------------------------------*/

function _HYPSSetFont (_font_face,_font_size)
{
	
	_res_string = "";
	_res_string * 64;
	_res_string * ("/"+_font_face+" findfont\n");
	_res_string * ("/fs "+_font_size+" def\nfs scalefont\nsetfont\n");
	_res_string * 0;
	return _res_string;
}

/*---------------------------------------------------------
generates string centering commands

x y (text) centertext - to output (text) so that its center is at (x,y)

x y (text) righttext - to output (text) so that its right bottom edge is at (x,y)


---------------------------------------------------------*/

function _HYPSTextCommands (dummy)
{
	_res_string = "";
	_res_string * 64;
	_res_string * "/centertext {dup newpath 0 0 moveto false charpath closepath pathbbox pop exch pop exch sub 2 div 4 -1 roll exch sub 3 -1 roll newpath moveto show} def\n";
	_res_string * "/vcentertext {90 rotate centertext -90 rotate} def\n";
	_res_string * "/righttext  {dup newpath 0 0 moveto false charpath closepath pathbbox pop exch pop exch sub       4 -1 roll exch sub 3 -1 roll newpath moveto show} def\n";
	_res_string * 0;
	return _res_string;
}



/*--------------------------------------------------------*/

function determineCoordinateTicks (x1,x2) 
{
	_range 	   = x2-x1;
	_log10Tick = Log(_range)/Log(10) /* round to the next smallest integer */
				 $1;
				 
	_log10Tick = Exp(_log10Tick*Log(10));
	if (_range/_log10Tick < 4)
	{
		_log10Tick = _log10Tick / (((4*_log10Tick/_range)+0.5)$1);
	}
	return _log10Tick;
}


/*--------------------------------------------------------*/


function ScatterPlot		 (xy&, 			/* Nx2 matrix with x,y,value points to plot */
							  xyranges, 	/* 2x2 matrix {{x_min, x_max}{y_min, y_max} 
							  				   will be adjusted to cover the data in xy if needed*/
							  plotDim, 		/* 1x3 matrix {{width, height,font_size}} of the plot in points */
							  colors, 		/* Nx3 matrix of RGB colors to plot each point with */
							  shapes, 		/* Nx1 matrix of shapes to plot for each point */
							  labels  		/* 1x3 matrix of strings: plot-label, x-axis label, y-axis label*/
							  )
{
	
	psDensityPlot = ""; psDensityPlot*1024;
	
	plotHeight = Max (100, plotDim[1]);
	plotWidth  = Max (100, plotDim[0]);
	
	plotOriginX = 4.5*plotDim[2];
	plotOriginY = 3.5*plotDim[2];
	
	xMin		= xyranges[0][0];
	xMax		= xyranges[0][1];
	yMin		= xyranges[1][0];
	yMax		= xyranges[1][1];
	
	psDensityPlot * _HYPSPageHeader (plotWidth + 5*plotDim[2], plotHeight + 4*plotDim[2], "Density Plot");
	psDensityPlot * "\n";
	psDensityPlot * _HYPSSetFont ("Times-Roman", plotDim[2]);
	psDensityPlot * "\n";
	psDensityPlot * _HYPSTextCommands(0);
	
	psDensityPlot * "\n 1 setlinewidth 1 setlinecap 0 setlinejoin 0 0 0 setrgbcolor";
	psDensityPlot * ("\n " + plotOriginX + " " + plotOriginY + " " + plotWidth + " " + plotHeight + " rectstroke\n");
	
	/* adjust data ranges if necessary */
	
	_x = Rows (xy);

	for (_dataPoint = 0; _dataPoint < _x; _dataPoint = _dataPoint + 1)
	{
		xMin = Min(xMin,xy[_dataPoint][0]);
		xMax = Max(xMax,xy[_dataPoint][0]);
		yMin = Min(yMin,xy[_dataPoint][1]);
		yMax = Max(yMax,xy[_dataPoint][1]);
	}
	
	px = plotWidth /(xMax-xMin);
	py = plotHeight/(yMax-yMin);
	
	

	for (_dataPoint = 0; _dataPoint < _x; _dataPoint = _dataPoint + 1)
	{
		psDensityPlot * (""+ colors[_dataPoint][0] + " " + colors[_dataPoint][1] + " " + colors[_dataPoint][2] + " setrgbcolor\n");

		psDensityPlot * ("newpath " + (plotOriginX+(xy[_dataPoint][0]-xMin)*px) + " " 
									+ (plotOriginY+(xy[_dataPoint][1]-yMin)*py) + " " 
									+ "1 1 rectstroke\n");
	
	}
	

	xscaler = determineCoordinateTicks (xMin,xMax);
	_x	= ((xMin/xscaler)$1)*xscaler;
	psDensityPlot * ("0 0 0 setrgbcolor\n");
	while (_x < xMax)
	{
		xStep = (plotOriginX + px*(_x-xMin));
		psDensityPlot * ("" +  xStep + " " + (2.5*plotDim[2]) + " (" + Format(_x,4,2) + ") centertext\n");  
		psDensityPlot * ("" +  xStep + " " + (plotOriginY+0.25*plotDim[2]) + " moveto 0 "
							+ (-0.25*plotDim[2]) +" rlineto stroke\n");  
		_x = _x + xscaler;
	}
	
	yscaler = determineCoordinateTicks (yMin,yMax);
	_y	= ((yMin/yscaler)$1)*yscaler;
	while (_y < yMax)
	{
		yStep = (plotOriginY + py*(_y-yMin));
		psDensityPlot * ("" +  (4*plotDim[2]) + " " + yStep + " (" + Format(_y,4,2) + ") righttext\n");  
		psDensityPlot * ("" +  plotOriginX    + " " + yStep + " moveto "+(0.25*plotDim[2]) +" 0 rlineto stroke\n");  
		_y = _y + yscaler;
	}

	psDensityPlot * ("" + (plotOriginX+plotWidth/2) + " " + (0.5*plotDim[2]) +" (" + labels[1] + ") centertext\n");
	psDensityPlot * ("" + (plotOriginY+plotHeight/2) + " " + (-1.5*plotDim[2]) +" ("+ labels[2] + ") vcentertext\n");	
	psDensityPlot * "\nshowpage\n";
	psDensityPlot * 0;
	
	return psDensityPlot;
}
