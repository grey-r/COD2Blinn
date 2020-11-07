import sys, os.path

try:
    import PIL
    import numpy as np
    from PIL import Image, ImageOps, ImageChops
except ImportError:
    sys.exit("""You need PIL!
                install it from http://pypi.python.org/pypi/Pillow
                or run pip install Pillow.""")

VMT = '''"VertexLitGeneric"
{{
	$basetexture	"models/weapons/tfa_cod/mwr/{name}_d"
	$bumpmap	"models/weapons/tfa_cod/mwr/{name}_n"
	$phongexponenttexture	"models/weapons/tfa_cod/mwr/{name}_s"

	$phong	"1"
	$phongboost	"4"
	$phongfresnelranges	"[.78 .9 1]"

	// $detail "path/to/camo/pattern"
	// $detailblendmode	"4"
	// $detailscale	"1"

	$envmap	"env_cubemap"
	$envmaptint	"[.25 .25 .25]"
	$normalmapalphaenvmapmask	"1"
	$envmapfresnel	"1"

	$rimlight	"1"
	$rimmask	"1"
	$rimlightboost	"1"
	$rimlightexponent	"33"
}}'''

def execCamo(imageAr,outDir="./",fn="gun"):
    #prepare output directory
    finalOutDir = os.path.join(outDir,"out/")
    if not os.path.exists(finalOutDir):
        os.makedirs(finalOutDir)

    #get maximum sizes
    wMax = 0
    hMax = 0
    for im in imageAr:
        wMax = max(im.width,wMax)
        hMax = max(im.height,hMax)
    
    #scale all to maximum size
    for k in range(len(imageAr)):
        im = imageAr[k]
        if (im.width<wMax or im.height<hMax):
            imageAr[k] = im.resize((wMax,hMax), resample = PIL.Image.LANCZOS)
    
    #extract channels
    diffuse = imageAr[0].convert(mode="RGB")
    mask = imageAr[1].convert(mode="RGB")
    normal = imageAr[2].convert(mode="RGB")
    occlusion = imageAr[3].convert(mode="RGB")
    specular = imageAr[4]

    #channel extraction
    specSplit = specular.convert(mode="RGBA").split()
    glossL = specSplit[3]
    gloss = glossL.convert(mode="RGB")
    specularRGB=specular.convert(mode="RGB")

    #utils
    white = Image.new("L", (wMax,hMax), (255))
    black = Image.new("L", (wMax,hMax), (0))

    #diffuse=diffuse*ao*spec
    #diffuse alpha = inv mask
    finalDiffuse = ImageChops.blend(diffuse,specularRGB,0.25)
    finalDiffuse = ImageChops.multiply(finalDiffuse,occlusion)
    finalDiffuse = finalDiffuse.convert(mode="RGBA")
    finalDiffuse.putalpha(ImageOps.invert(mask).convert(mode="L"))
    finalDiffuse.save(os.path.join(outDir,"out",fn+"_d.tga"),"TGA")

    #normal
    #normal alpha = gloss*spec
    finalNormal = normal.convert(mode="RGBA")
    normalAlpha = ImageChops.multiply(ImageChops.multiply(specularRGB, gloss ), occlusion).convert(mode="L")
    finalNormal.putalpha( normalAlpha )
    finalNormal.save(os.path.join(outDir,"out",fn+"_n.tga"),"TGA")

    #s={gloss,255,0,gloss*spec}
    glossAr = np.array(gloss, dtype=np.uint8)

    # Make a LUT (Look-Up Table) to translate image values
    lut_in = [0, 162, 208, 255]
    lut_out = [0, 16, 64, 255]
    LUT=np.interp(np.arange(0, 256), lut_in, lut_out).astype(np.uint8)

    # Apply LUT and cache resulting image
    glossSource = Image.fromarray(LUT[glossAr]).convert(mode="L")

    finalSpec = Image.merge("RGBA", [ glossSource, white, black, normalAlpha ])
    finalSpec.save(os.path.join(outDir,"out",fn+"_s.tga"),"TGA")

    #vmt
    vmtFile = open(os.path.join(outDir,"out","mtl_"+fn+".vmt"), 'w')
    vmtFile.write(VMT.format(name=fn))
    vmtFile.close()

    
def runCamo(baseDiffusePath):
    if not os.path.isfile(baseDiffusePath):
        exit("THATS NO FILE")
    directory = os.path.dirname(baseDiffusePath)
    base=os.path.basename(baseDiffusePath)
    baseDecomp=os.path.splitext(base)
    occPath=""
    specPath=""
    nrmPath=""
    maskPath=""
    specSearch=[]
    occSearch=[]
    nrmSearch=[]
    maskSearch=[]
    if baseDecomp[0].lower().endswith("_col"):
        baseFN = baseDecomp[0][0:-4]
        #maskPath = os.path.join(directory,baseFN+"_mask_01"+baseDecomp[1])
        #specPath = os.path.join(directory,baseFN+"_S"+baseDecomp[1])
        #nrmPath = os.path.join(directory,baseFN+"_nml"+baseDecomp[1])
        specSearch.append(baseFN+"_spc")
        occSearch.append(baseFN+"_occ")
        nrmSearch.append(baseFN+"_nml")
        maskSearch.append(baseFN+"_mask")
        if baseFN.find("frame"):
            rep=baseFN.replace("frame","body")
            specSearch.append(rep+"_spc")
            occSearch.append(rep+"_occ")
            nrmSearch.append(rep+"_nml")
            maskSearch.append(rep+"_mask")
        if baseFN.find("body"):
            rep=baseFN.replace("body","frame")
            specSearch.append(rep+"_spc")
            occSearch.append(rep+"_occ")
            nrmSearch.append(rep+"_nml")
            maskSearch.append(rep+"_mask")
    for f in os.listdir(directory):
        found=False
        for s in specSearch:
            if (f.find(s)!=-1):
                specPath = os.path.join(directory,f)
                print("Found specular file: " + f)
                found=True
                break
        if (found):
            continue
        for s in occSearch:
            if (f.find(s)!=-1):
                occPath = os.path.join(directory,f)
                print("Found occlusion file: " + f)
                found=True
                break
        if (found):
            continue
        for s in nrmSearch:
            if (f.find(s)!=-1):
                nrmPath = os.path.join(directory,f)
                print("Found normal file: " + f)
                found=True
                break
        if (found):
            continue
        for s in maskSearch:
            if (f.find(s)!=-1):
                maskPath = os.path.join(directory,f)
                print("Found mask file: " + f)
                found=True
                break
        if (found):
            continue
    
    fnv = baseDecomp[0].lower()[0:-4]
    fnv = fnv.replace("frame","body")
    
    d = Image.open(baseDiffusePath)
    if os.path.isfile(maskPath):
        m=Image.open(maskPath)
        fnv=fnv+"_camo"
    else:
        print("WARNING: MISSING MASK")
        m=Image.new("RGB", (512,512), color=(0,0,0))
    if os.path.isfile(specPath):
        s=Image.open(specPath)
    else:
        print("WARNING: MISSING SPECULAR")
        s=Image.new("RGB", (512,512), color=(64,64,64))
    if os.path.isfile(occPath):
        o=Image.open(occPath)
    else:
        print("WARNING: MISSING OCCLUSION")
        o=Image.new("RGB", (512,512), color=(255,255,255))
    if os.path.isfile(nrmPath):
        n=Image.open(nrmPath)
    else:
        print("WARNING: MISSING NORMALS")
        n=Image.new("RGB", (512,512), color=(128,128,255))
    print("Running for " + fnv)
    execCamo([d,m,n,o,s],outDir=directory,fn=fnv)
if __name__ == "__main__":
    maskPath = ""
    specPath = ""
    nrmPath = ""

    m=None
    n=None
    o=None
    s=None

    args = sys.argv
    baseDiffusePath = None
    if len(args)>=2:
        baseDiffusePath=args[1]
    else:
        print("Input your diffuse texture path.")
        baseDiffusePath=input()
        if baseDiffusePath.startswith("\"") or baseDiffusePath.startswith("'"):
            baseDiffusePath=baseDiffusePath[1:]
        if baseDiffusePath.endswith("\"") or baseDiffusePath.endswith("'"):
            baseDiffusePath=baseDiffusePath[0:-1]
    if os.path.isfile(baseDiffusePath) and not os.path.isdir(baseDiffusePath):
        runCamo(baseDiffusePath)
    elif os.path.isdir(baseDiffusePath):
        for f in os.listdir(baseDiffusePath):
            if f.endswith("_col.tga"):
                runCamo(os.path.join(baseDiffusePath,f))