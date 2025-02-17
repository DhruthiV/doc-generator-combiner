import React, { useState, useEffect } from 'react';
import { Button, Card, Container, Row, Col } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css'
function App() {
  const [syllabi, setSyllabi] = useState([]);
  const [selectedSyllabi, setSelectedSyllabi] = useState([]);

  // Fetch syllabus data from backend
  useEffect(() => {
    fetch('http://localhost:5000/syllabi')
      .then((response) => response.json())
      .then((data) => setSyllabi(data.syllabi))
      .catch((error) => console.error("There was an error fetching the syllabi!", error));
  }, []);

  // Handle selecting and unselecting a syllabus card
  const toggleSelectSyllabus = (courseCode) => {
    setSelectedSyllabi((prev) => {
      if (prev.includes(courseCode)) {
        return prev.filter((code) => code !== courseCode);
      } else {
        return [...prev, courseCode];
      }
    });
  };

  // Handle downloading individual syllabus PDF
  const handleDownload = (courseCode) => {
    window.open(`http://localhost:5000/generate-pdf/${courseCode}`, '_blank');
  };

  // Handle combine PDFs
  const handleCombineAndDownload = () => {
    if (selectedSyllabi.length < 2) {
      alert("Please select at least 2 syllabi.");
      return;
    }
    window.open(`http://localhost:5000/combine-pdfs/${selectedSyllabi.join(',')}`, '_blank');
  };

  return (
    <Container>
      <Button
        variant="primary"
        className="my-3"
        onClick={handleCombineAndDownload}
        disabled={selectedSyllabi.length < 2}
      >
        Combine and Download Syllabus
      </Button>
      <Row>
        {syllabi.map((syllabus) => (
          <Col key={syllabus.course_code} md={4} className="mb-4">
            <Card
              style={{
                cursor: 'pointer',
                backgroundColor: selectedSyllabi.includes(syllabus.course_code) ? 'green' : 'lightgray',
                color: selectedSyllabi.includes(syllabus.course_code) ? 'white' : 'black',
              }}
              onClick={() => toggleSelectSyllabus(syllabus.course_code)}
            >
              <Card.Body>
                <Card.Title>{syllabus.course_code}</Card.Title>
                <Card.Text>
                  {syllabus.program} - {syllabus.year}
                </Card.Text>
                <Button
                  variant="primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownload(syllabus.course_code);
                  }}
                >
                  Download
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </Container>
  );
}

export default App;
