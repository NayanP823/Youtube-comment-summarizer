   import React, { useState } from 'react';
   import { motion, AnimatePresence } from 'framer-motion';
   import './App.css';

   function App() {
     const [videoUrl, setVideoUrl] = useState('');
     const [status, setStatus] = useState('ready'); // ready | loading | done | error
     const [result, setResult] = useState(null);
     const [error, setError] = useState('');

     const handleSubmit = async (e) => {
       e.preventDefault();
       setStatus('loading');
       setResult(null);
       setError('');
       try {
         const resp = await fetch('http://localhost:8000/summarize', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ video_url: videoUrl })
         });
         if (!resp.ok) throw new Error((await resp.json()).detail || 'Unknown error');
         const data = await resp.json();
         setResult(data);
         setStatus('done');
       } catch (err) {
         setError(err.message);
         setStatus('error');
       }
     };

     return (
       <div className="main-bg">
         <div className="container pop-glass">
           <motion.h1 initial={{ y: -80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ type: 'spring', stiffness: 80 }}>
             YouTube Comment Summarizer
           </motion.h1>

           <AnimatePresence>
             {status === 'ready' && (
               <motion.form
                 initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.2, opacity: 0 }}
                 onSubmit={handleSubmit}
               >
                 <input
                   type="text"
                   className="yt-input"
                   required
                   value={videoUrl}
                   onChange={e => setVideoUrl(e.target.value)}
                   placeholder="Paste YouTube video URL here..."
                 />
                 <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>Summarize 🚀</motion.button>
               </motion.form>
             )}
           </AnimatePresence>

           <AnimatePresence>
             {status === 'loading' && (
               <motion.div key="loading" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.7, opacity: 0 }} className="poppy-loader">
                 <div className="lds-ripple"><div></div><div></div></div>
                 <p>Working magic... <span role="img" aria-label="magic">✨</span></p>
               </motion.div>
             )}
           </AnimatePresence>

           {status === 'error' && (
             <motion.div className="error-box" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
               <p>Failed: {error}</p>
             </motion.div>
           )}
           {/* Summary Results */}
           <AnimatePresence>
             {status === 'done' && result && (
               <motion.div key="summary" initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -30, opacity: 0 }} className="result-pan pop-glass">
                 <h2>Summary</h2>
                 <div className="big-summary">{result.summary}</div>
                 <div className="senti-bar">
                   <span>Comments: <b>{result.n_comments}</b></span>
                   <span role="img" aria-label="Positive">👍</span> <b>{result.n_positive}</b> &nbsp;
                   <span role="img" aria-label="Negative">👎</span> <b>{result.n_negative}</b>
                 </div>
                 <details>
                   <summary>Show Summary Chunks</summary>
                   <div className="chunk-scroll">
                     {result.raw_summary_chunks.map((c, i) => <div key={i} className="chunk-one">{c}</div>)}
                   </div>
                 </details>
                 <button className="again-btn" onClick={() => { setVideoUrl(''); setResult(null); setStatus('ready'); }}>
                   Summarize another!
                 </button>
               </motion.div>
             )}
           </AnimatePresence>

          
         </div>
       </div>
     );
   }

   export default App;