import sys, os.path

try:
    import PIL
    from PIL import Image
except ImportError:
    sys.exit("""You need PIL!
                install it from http://pypi.python.org/pypi/Pillow
                or run pip install Pillow.""")

def exec5Stack(imageAr,outDir="./"):
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
    diffuse = imageAr[0]
    mask = imageAr[1]
    normal = imageAr[2]
    specular = imageAr[3]

    #split mask into components
    maskSplit = mask.split()
    bloodMask = maskSplit[0] # unused
    gloss = maskSplit[1]
    ao = maskSplit[2]   
    emissive = envRGBTMP=Image.new("L", (wMax,hMax), color=0)
    if len(maskSplit)>3:
        emissive=maskSplit[3]

    #composite final textures


    #diffuse=diffuse*ao
    finalDiffuse = PIL.ImageChops.multiply(diffuse.convert(mode="RGB"),ao.convert(mode="RGB")).convert(mode="RGBA")
    finalDiffuse.putalpha(emissive)
    finalDiffuse.save(os.path.join(outDir,"out/dif.tga"),"TGA")
 
    #envMasks=spec*spec*ao
    env = PIL.ImageChops.multiply(specular.convert(mode="RGB"),specular.convert(mode="RGB"))
    env = PIL.ImageChops.multiply(env,ao.convert(mode="RGB"))
    #split env into channels
    envSplit = env.split()
    envRed = envSplit[0]
    envGreen = envSplit[1]
    envBlue = envSplit[2]
    #save each env channel as rgba
    envRGBTMP=Image.new("RGBA", (wMax,hMax), color=0)
    #r
    envRGBTMP.putalpha(envRed)
    envRGBTMP.save(os.path.join(outDir,"out/env_r.tga"),"TGA")
    #g
    envRGBTMP.putalpha(envGreen)
    envRGBTMP.save(os.path.join(outDir,"out/env_g.tga"),"TGA")
    #b
    envRGBTMP.putalpha(envBlue)
    envRGBTMP.save(os.path.join(outDir,"out/env_b.tga"),"TGA")

    #normals
    #normal alpha = gloss - used for fresnel
    normalAlpha = gloss.convert(mode="L")
    finalNormal = normal.convert(mode="RGBA")
    finalNormal.putalpha(normalAlpha)
    finalNormal.save(os.path.join(outDir,"out/norm.tga"),"TGA")

    #spec = spec???? lol
    finalSpec = specular.convert(mode="RGB")
    finalSpec.save(os.path.join(outDir,"out/spec.tga"),"TGA")

    #mask
    white = Image.new("L", (wMax,hMax), color="white")
    finalMask = Image.merge("RGB", (PIL.ImageChops.multiply(gloss,gloss),white,white))
    finalMask.save(os.path.join(outDir,"out/mask.tga"),"TGA")
    

if __name__ == "__main__":
    maskPath = ""
    specPath = ""
    nrmPath = ""

    m=None
    n=None
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
    if not os.path.isfile(baseDiffusePath):
        exit("THATS NO FILE")
    directory = os.path.dirname(baseDiffusePath)
    base=os.path.basename(baseDiffusePath)
    baseDecomp=os.path.splitext(base)
    if baseDecomp[0].lower().endswith("_d"):
        baseFN = baseDecomp[0][0:-2]
        maskPath = os.path.join(directory,baseFN+"_M"+baseDecomp[1])
        specPath = os.path.join(directory,baseFN+"_S"+baseDecomp[1])
        nrmPath = os.path.join(directory,baseFN+"_N"+baseDecomp[1])
    
    d = Image.open(baseDiffusePath)
    if os.path.isfile(maskPath):
        m=Image.open(maskPath)
    else:
        print("WARNING: MISSING MASK")
        m=Image.new("RGB", (512,512), color=(192,64,255))
    if os.path.isfile(specPath):
        s=Image.open(specPath)
    else:
        print("WARNING: MISSING SPECULAR")
        s=Image.new("RGB", (512,512), color=(64,64,64))
    if os.path.isfile(nrmPath):
        n=Image.open(nrmPath)
    else:
        print("WARNING: MISSING NORMALS")
        n=Image.new("RGB", (512,512), color=(128,128,255))
    exec5Stack([d,m,n,s],outDir=directory)