# 🚀 Deployment Guide

## Quick Deploy Options

### Option 1: Railway (Recommended - Free)
1. **Sign up** at [railway.app](https://railway.app)
2. **Connect GitHub** repository
3. **Deploy automatically** - Railway detects Python/FastAPI
4. **Set environment variables** (if needed):
   - `PORT=8001`
   - `PYTHONPATH=/app`

### Option 2: Render (Free Tier)
1. **Sign up** at [render.com](https://render.com)
2. **Create new Web Service**
3. **Connect GitHub** repository
4. **Configure**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python api/main.py`
   - **Environment**: Python 3.9 (specified in runtime.txt)

### Option 3: Vercel (Free)
1. **Sign up** at [vercel.com](https://vercel.com)
2. **Import GitHub** repository
3. **Configure** as Python project
4. **Deploy** automatically

## Local Testing Before Deploy

```bash
# Test the application locally
python api/main.py

# Test endpoints
curl http://localhost:8001/api/health
curl "http://localhost:8001/api/search?q=programming"
```

## Production Checklist

- ✅ **CI/CD Pipeline** - GitHub Actions configured
- ✅ **Health Checks** - `/api/health` endpoint
- ✅ **Performance** - Sub-1ms search times
- ✅ **Documentation** - README.md complete
- ✅ **Docker** - Dockerfile ready
- ✅ **Monitoring** - Metrics endpoint available

## Environment Variables

```bash
# Optional: Set custom port
PORT=8001

# Optional: Set Python path
PYTHONPATH=/app
```

## Post-Deployment

1. **Test the live URL**
2. **Check health endpoint**: `https://your-app.railway.app/api/health`
3. **Test search**: `https://your-app.railway.app/api/search?q=programming`
4. **Update README** with live URL
5. **Share on resume**! 🎉

## Troubleshooting

**If deployment fails:**
1. Check logs for Python version issues
2. Ensure `requirements.txt` is up to date
3. Verify `api/main.py` runs locally
4. Check platform-specific requirements

**Performance issues:**
- The app is optimized for sub-1ms performance
- 512MB RAM should be sufficient
- Consider upgrading if you get high traffic

---

**Ready to deploy! Your 9/10 project is production-ready! 🚀** 